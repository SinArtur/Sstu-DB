"""
Parser for SSTU schedule website.
"""
import re
import logging
from datetime import datetime, time, date, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

# Try to import SOCKS support
try:
    import socks
    import socket
    from urllib3.contrib.socks import SOCKSProxyManager
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SSTUScheduleParser:
    """Parser for rasp.sstu.ru schedule."""
    
    BASE_URL = "https://rasp.sstu.ru"
    MAIN_PAGE = f"{BASE_URL}/"
    GROUP_PAGE = f"{BASE_URL}/rasp/group/"
    TEACHER_PAGE = f"{BASE_URL}/rasp/teacher/"
    
    # Время пар
    LESSON_TIMES = {
        1: (time(8, 0), time(9, 30)),
        2: (time(9, 45), time(11, 15)),
        3: (time(11, 30), time(13, 0)),
        4: (time(13, 40), time(15, 10)),
        5: (time(15, 20), time(16, 50)),
        6: (time(17, 0), time(18, 30)),
        7: (time(18, 40), time(20, 10)),  # 7-я пара
    }
    
    # Маппинг типов занятий
    LESSON_TYPE_MAP = {
        'лек': 'лек',
        'лекц': 'лек',
        'пр': 'пр',
        'прак': 'пр',
        'лаб': 'лаб',
        'экз': 'экз',
        'конс': 'конс',
        'зач': 'экз',  # Зачет как экзамен
        'установочная лекция': 'лек',
    }
    
    # Маппинг дней недели
    WEEKDAY_MAP = {
        'понедельник': 1,
        'вторник': 2,
        'среда': 3,
        'четверг': 4,
        'пятница': 5,
        'суббота': 6,
        'воскресенье': 7,
    }
    
    def __init__(self, timeout: int = 30, proxy: Optional[str] = None):
        """Initialize parser with timeout and optional proxy."""
        self.timeout = timeout
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if self.proxy:
            # Support both HTTP and SOCKS5 proxies
            if self.proxy.startswith('socks5://') or self.proxy.startswith('socks4://'):
                # SOCKS proxy - requires PySocks package
                if not SOCKS_AVAILABLE:
                    logger.error("SOCKS proxy requires 'PySocks' package. Install with: pip install PySocks")
                    raise ImportError("PySocks is required for SOCKS proxy support")
                
                # requests automatically detects SOCKS proxy format when PySocks is installed
                # Just set it in proxies dict
                self.session.proxies = {
                    'http': self.proxy,
                    'https': self.proxy
                }
                logger.info(f"Using SOCKS proxy: {self.proxy}")
            else:
                # HTTP proxy
                self.session.proxies = {
                    'http': self.proxy,
                    'https': self.proxy
                }
                logger.info(f"Using HTTP proxy: {self.proxy}")
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse page with retry logic."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'html.parser')
            except requests.Timeout as e:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    continue
                logger.error(f"Failed to fetch {url} after {retries} attempts")
            except requests.RequestException as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    continue
                if self.proxy:
                    logger.warning(f"Using proxy: {self.proxy}")
            return None
        return None
    
    def parse_main_page(self) -> List[Dict]:
        """Parse main page to get all institutes and groups."""
        soup = self.fetch_page(self.MAIN_PAGE)
        if not soup:
            return []
        
        institutes_data = []
        accordion = soup.find('div', {'id': 'raspStructure'})
        if not accordion:
            logger.warning("Could not find schedule structure")
            return []
        
        for card in accordion.find_all('div', class_='card'):
            institute_data = self._parse_institute_card(card)
            if institute_data:
                institutes_data.append(institute_data)
        
        logger.info(f"Parsed {len(institutes_data)} institutes")
        return institutes_data
    
    def _parse_institute_card(self, card) -> Optional[Dict]:
        """Parse single institute card."""
        try:
            header = card.find('div', class_='card-header')
            if not header:
                return None
            
            institute_div = header.find('div', class_='institute')
            if not institute_div:
                return None
            
            institute_name = institute_div.get_text(strip=True)
            
            # Extract institute ID from collapse target
            heading_id = header.get('id', '')
            institute_id = None
            if heading_id.startswith('heading'):
                try:
                    institute_id = int(heading_id.replace('heading', ''))
                except ValueError:
                    pass
            
            body = card.find('div', class_='card-body')
            if not body:
                return None
            
            groups = self._parse_groups_from_body(body)
            
            return {
                'name': institute_name,
                'sstu_id': institute_id,
                'groups': groups
            }
        except Exception as e:
            logger.error(f"Error parsing institute card: {e}")
            return None
    
    def _parse_groups_from_body(self, body) -> List[Dict]:
        """Parse groups from institute card body."""
        groups = []
        
        current_edu_form = 'full_time'  # default
        current_degree = 'bachelor'  # default
        
        # Use descendants to get all elements in document order
        for element in body.descendants:
            if not hasattr(element, 'get'):
                continue
            
            # Check for education form
            if element.has_attr('class') and 'edu-form' in element.get('class', []):
                form_text = element.get_text(strip=True).lower()
                # Be more precise with detection
                if 'очно-заочн' in form_text or 'заочн' in form_text and 'сокращ' in form_text:
                    current_edu_form = 'evening'
                elif 'заочн' in form_text:
                    current_edu_form = 'part_time'
                elif 'очн' in form_text:
                    current_edu_form = 'full_time'
            
            # Check for degree type
            if element.has_attr('class') and 'group-type' in element.get('class', []):
                degree_text = element.get_text(strip=True).lower()
                if 'бакалавриат' in degree_text:
                    current_degree = 'bachelor'
                elif 'магистратура' in degree_text:
                    current_degree = 'master'
                elif 'специалитет' in degree_text:
                    current_degree = 'specialty'
                elif 'аспирантура' in degree_text:
                    current_degree = 'postgraduate'
            
            # Parse groups - look for div.groups class
            if element.has_attr('class') and 'groups' in element.get('class', []):
                # Find all group links within this groups div
                group_links = element.find_all('a')
                for link in group_links:
                    group_name = link.get_text(strip=True)
                    if not group_name:  # Skip empty links
                        continue
                        
                    group_url = link.get('href', '')
                    
                    # Extract group ID from URL
                    group_id = None
                    if '/rasp/group/' in group_url:
                        try:
                            group_id = int(group_url.split('/rasp/group/')[-1].split('/')[0])
                        except (ValueError, IndexError):
                            pass
                    
                    # Extract course number from group name
                    course_match = re.search(r'-(\d)1$', group_name)
                    course_number = int(course_match.group(1)) if course_match else None
                    
                    # Avoid duplicates
                    if not any(g['name'] == group_name for g in groups):
                        groups.append({
                            'name': group_name,
                            'sstu_id': group_id,
                            'education_form': current_edu_form,
                            'degree_type': current_degree,
                            'course_number': course_number,
                        })
        
        return groups
    
    def parse_group_schedule(self, group_id: int) -> List[Dict]:
        """Parse schedule for specific group."""
        url = f"{self.GROUP_PAGE}{group_id}"
        soup = self.fetch_page(url)
        if not soup:
            return []
        
        lessons = []
        calendar = soup.find('div', class_='calendar')
        if not calendar:
            logger.warning(f"No calendar found for group {group_id}")
            return []
        
        # Parse exam warnings
        exam_dates = self._parse_exam_warnings(calendar)
        
        # Parse weekly schedule
        for week_div in calendar.find_all('div', class_='week'):
            week_lessons = self._parse_week(week_div, exam_dates)
            lessons.extend(week_lessons)
        
        logger.info(f"Parsed {len(lessons)} lessons for group {group_id}")
        return lessons
    
    def _parse_exam_warnings(self, calendar) -> Dict[str, datetime]:
        """Parse exam dates from warnings."""
        exam_dates = {}
        warnings = calendar.find('div', class_='lesson-warnings')
        if not warnings:
            return exam_dates
        
        warning_texts = warnings.find_all('div', class_='lesson-warning-text')
        for text in warning_texts:
            content = text.get_text(strip=True)
            # Extract subject and date: "Предмет (12.01.2026)"
            match = re.match(r'(.+?)\s*\((\d{2}\.\d{2}\.\d{4})\)', content)
            if match:
                subject_name = match.group(1).strip()
                date_str = match.group(2)
                try:
                    exam_date = datetime.strptime(date_str, '%d.%m.%Y')
                    exam_dates[subject_name] = exam_date
                except ValueError:
                    pass
        
        return exam_dates
    
    def _parse_week(self, week_div, exam_dates: Dict) -> List[Dict]:
        """Parse single week schedule."""
        lessons = []
        
        # Get week number from data-lesson attribute (e.g., "w03n1" -> week 3)
        week_number = None
        first_lesson_div = week_div.find('div', class_='day-lesson', attrs={'data-lesson': re.compile(r'w(\d+)n\d+')})
        if first_lesson_div:
            data_lesson = first_lesson_div.get('data-lesson', '')
            match = re.search(r'w(\d+)n\d+', data_lesson)
            if match:
                try:
                    week_number = int(match.group(1))
                except ValueError:
                    pass
        
        days = week_div.find_all('div', class_='day', recursive=False)
        
        for day_div in days:
            # Skip hour column
            if 'day-header-color-blue' in day_div.get('class', []):
                continue
            
            day_data = self._parse_day(day_div, exam_dates, week_number)
            lessons.extend(day_data)
        
        return lessons
    
    def _parse_day(self, day_div, exam_dates: Dict, week_number: Optional[int]) -> List[Dict]:
        """Parse single day schedule."""
        lessons = []
        
        # Get day name and date
        header = day_div.find('div', class_='day-header')
        if not header:
            return lessons
        
        # Get text from header - может быть вложенный div
        # Структура: <div class="day-header"><div><span>Понедельник</span>12.01</div></div>
        header_inner = header.find('div')
        if header_inner:
            # Берем весь текст из внутреннего div (включая текст после span)
            header_text = header_inner.get_text(strip=True).lower()
        else:
            # Если нет внутреннего div, берем текст напрямую из header
            header_text = header.get_text(strip=True).lower()
        
        # Если текст пустой, пробуем найти span и текст после него
        if not header_text or not re.search(r'\d{2}\.\d{2}', header_text):
            span = header.find('span')
            if span:
                # Берем текст после span
                span_text = span.get_text(strip=True)
                # Ищем дату в родительском элементе после span
                parent_text = header_inner.get_text(strip=True) if header_inner else header.get_text(strip=True)
                if parent_text and parent_text != span_text:
                    header_text = parent_text.lower()
        
        # Extract weekday
        weekday = None
        for day_name, day_num in self.WEEKDAY_MAP.items():
            if day_name in header_text:
                weekday = day_num
                break
        
        if not weekday:
            return lessons
        
        # Extract date from header (e.g., "Понедельник 12.01" -> date(2026, 1, 12))
        day_date = None
        date_match = re.search(r'(\d{2})\.(\d{2})', header_text)
        if date_match:
            day_str = date_match.group(1)
            month_str = date_match.group(2)
            try:
                # Определяем год: если месяц январь-февраль и сейчас конец года, то это следующий год
                # Иначе используем текущий год
                current_year = datetime.now().year
                current_month = datetime.now().month
                parsed_month = int(month_str)
                parsed_day = int(day_str)
                
                # Если парсим январь-февраль, а сейчас ноябрь-декабрь, то это следующий год
                if parsed_month <= 2 and current_month >= 11:
                    year = current_year + 1
                # Если парсим ноябрь-декабрь, а сейчас январь-февраль, то это прошлый год
                elif parsed_month >= 11 and current_month <= 2:
                    year = current_year - 1
                else:
                    year = current_year
                
                day_date = date(year, parsed_month, parsed_day)
                logger.debug(f"Parsed date from header '{header_text}': {day_date}")
            except ValueError as e:
                logger.error(f"Error parsing date from header '{header_text}': {e}")
                # Не пропускаем день, просто не устанавливаем дату
                pass
        else:
            logger.warning(f"Could not find date in header text: '{header_text}'")
        
        # Parse lessons
        lesson_divs = day_div.find_all('div', class_='day-lesson', recursive=False)
        for lesson_div in lesson_divs:
            # Skip empty lessons
            if 'day-lesson-empty' in lesson_div.get('class', []):
                continue
            
            lesson_data = self._parse_lesson(lesson_div, weekday, week_number, exam_dates, day_date)
            if lesson_data:
                # Убеждаемся, что дата установлена
                if not lesson_data.get('specific_date') and day_date:
                    lesson_data['specific_date'] = day_date
                    logger.debug(f"Set specific_date from day_date: {day_date} for lesson {lesson_data.get('subject_name')}")
                lessons.append(lesson_data)
        
        # Логируем, если день не имеет даты, но есть занятия
        if lessons and not day_date:
            logger.warning(f"Day with {len(lessons)} lessons has no date! Header text was: '{header_text}'")
        
        return lessons
    
    def _parse_lesson(self, lesson_div, weekday: int, week_number: Optional[int], exam_dates: Dict, day_date: Optional[date] = None) -> Optional[Dict]:
        """Parse single lesson."""
        try:
            # Get lesson number from data attribute
            data_lesson = lesson_div.get('data-lesson', '')
            lesson_number = None
            if data_lesson:
                # Format: w03n1 -> lesson 1
                match = re.search(r'n(\d+)', data_lesson)
                if match:
                    lesson_number = int(match.group(1))
            
            if not lesson_number or lesson_number not in self.LESSON_TIMES:
                return None
            
            # Get lesson times
            start_time, end_time = self.LESSON_TIMES[lesson_number]
            
            # Find lesson details
            inner_div = lesson_div.find('div', recursive=False)
            if not inner_div:
                return None
            
            # Extract room
            room_div = inner_div.find('div', class_='lesson-room')
            room = room_div.get_text(strip=True) if room_div else ''
            
            # Extract subject name
            name_div = inner_div.find('div', class_='lesson-name')
            subject_name = name_div.get_text(strip=True) if name_div else ''
            
            if not subject_name:
                return None
            
            # Extract lesson type
            type_div = inner_div.find('div', class_='lesson-type')
            lesson_type_raw = type_div.get_text(strip=True) if type_div else ''
            lesson_type_raw = lesson_type_raw.strip('()')
            lesson_type = self.LESSON_TYPE_MAP.get(lesson_type_raw.lower(), 'other')
            
            # Extract teacher
            teacher_link = inner_div.find('a')
            teacher_name = None
            teacher_id = None
            teacher_url = None
            
            if teacher_link:
                teacher_name = teacher_link.get_text(strip=True)
                teacher_url = teacher_link.get('href', '')
                # Extract teacher ID from URL
                teacher_id_match = re.search(r'teachers/(\d+)-', teacher_url)
                if teacher_id_match:
                    try:
                        teacher_id = int(teacher_id_match.group(1))
                    except ValueError:
                        pass
            
            # Определяем specific_date:
            # 1. Для экзаменов - из exam_dates
            # 2. Для всех остальных - из day_date (дата из заголовка дня)
            specific_date = None
            if lesson_type == 'экз' and subject_name in exam_dates:
                specific_date = exam_dates[subject_name].date()
            elif day_date:
                # Для обычных занятий используем дату из заголовка дня
                specific_date = day_date
            
            # Вычисляем week_number на основе даты дня, если она есть (для обратной совместимости)
            final_week_number = week_number
            if day_date:
                semester_start = date(2026, 1, 12)  # Понедельник, начало семестра
                days_diff = (day_date - semester_start).days
                calculated_week = (days_diff // 7) + 1
                if calculated_week > 0:
                    final_week_number = calculated_week
            
            return {
                'subject_name': subject_name,
                'teacher_name': teacher_name,
                'teacher_id': teacher_id,
                'teacher_url': teacher_url if teacher_url and not teacher_url.startswith('http') else f"{self.BASE_URL}{teacher_url}" if teacher_url else None,
                'lesson_type': lesson_type,
                'room': room,
                'weekday': weekday,
                'lesson_number': lesson_number,
                'start_time': start_time,
                'end_time': end_time,
                'specific_date': specific_date,
                'week_number': final_week_number,
            }
        except Exception as e:
            logger.error(f"Error parsing lesson: {e}")
            return None
    
    def parse_teacher_schedule(self, teacher_id: int) -> List[Dict]:
        """Parse schedule for specific teacher."""
        url = f"{self.TEACHER_PAGE}{teacher_id}"
        soup = self.fetch_page(url)
        if not soup:
            return []
        
        lessons = []
        calendar = soup.find('div', class_='calendar')
        if not calendar:
            logger.warning(f"No calendar found for teacher {teacher_id}")
            return []
        
        # Parse exam/test warnings
        exam_dates = self._parse_exam_warnings(calendar)
        
        # Parse weekly schedule
        for week_div in calendar.find_all('div', class_='week'):
            week_lessons = self._parse_week_teacher(week_div, exam_dates)
            lessons.extend(week_lessons)
        
        logger.info(f"Parsed {len(lessons)} lessons for teacher {teacher_id}")
        return lessons
    
    def _parse_week_teacher(self, week_div, exam_dates: Dict) -> List[Dict]:
        """Parse single week schedule for teacher."""
        lessons = []
        
        days = week_div.find_all('div', class_='day', recursive=False)
        
        for day_div in days:
            # Skip hour column
            if 'day-header-color-blue' in day_div.get('class', []):
                continue
            
            day_data = self._parse_day_teacher(day_div, exam_dates)
            lessons.extend(day_data)
        
        return lessons
    
    def _parse_day_teacher(self, day_div, exam_dates: Dict) -> List[Dict]:
        """Parse single day schedule for teacher."""
        lessons = []
        
        # Get day name
        header = day_div.find('div', class_='day-header')
        if not header:
            return lessons
        
        header_text = header.get_text(strip=True).lower()
        
        # Extract weekday
        weekday = None
        for day_name, day_num in self.WEEKDAY_MAP.items():
            if day_name in header_text:
                weekday = day_num
                break
        
        if not weekday:
            return lessons
        
        # Parse lessons
        lesson_divs = day_div.find_all('div', class_='day-lesson', recursive=False)
        for lesson_div in lesson_divs:
            # Skip empty lessons
            if 'day-lesson-empty' in lesson_div.get('class', []):
                continue
            
            lesson_data = self._parse_lesson_teacher(lesson_div, weekday, exam_dates)
            if lesson_data:
                # For teacher schedule, one lesson div may contain multiple groups
                # We need to create separate lesson for each group
                if isinstance(lesson_data, list):
                    lessons.extend(lesson_data)
                else:
                    lessons.append(lesson_data)
        
        return lessons
    
    def _parse_lesson_teacher(self, lesson_div, weekday: int, exam_dates: Dict):
        """Parse single lesson for teacher (may have multiple groups)."""
        try:
            # Get lesson number
            data_lesson = lesson_div.get('data-lesson', '')
            lesson_number = None
            if data_lesson:
                match = re.search(r'n(\d+)', data_lesson)
                if match:
                    lesson_number = int(match.group(1))
            
            if not lesson_number or lesson_number not in self.LESSON_TIMES:
                return None
            
            start_time, end_time = self.LESSON_TIMES[lesson_number]
            
            inner_div = lesson_div.find('div', recursive=False)
            if not inner_div:
                return None
            
            # Extract room
            room_div = inner_div.find('div', class_='lesson-room')
            room = room_div.get_text(strip=True) if room_div else ''
            
            # Extract subject name
            name_div = inner_div.find('div', class_='lesson-name')
            subject_name = name_div.get_text(strip=True) if name_div else ''
            
            if not subject_name:
                return None
            
            # Extract lesson type
            type_div = inner_div.find('div', class_='lesson-type')
            lesson_type_raw = type_div.get_text(strip=True) if type_div else ''
            lesson_type_raw = lesson_type_raw.strip('()')
            lesson_type = self.LESSON_TYPE_MAP.get(lesson_type_raw.lower(), 'other')
            
            # Find groups - they are in lesson-room elements with mt-2 or lesson-room-1 class
            group_divs = inner_div.find_all('div', class_=['lesson-room', 'lesson-room-1'])
            groups = []
            
            for group_div in group_divs:
                if 'mt-2' in group_div.get('class', []) or 'lesson-room-1' in group_div.get('class', []):
                    group_text = group_div.get_text(strip=True)
                    # Extract group name from "Подгр. 1: б-ЗМКДз-11" or just "б-ЗМКДз-11"
                    if 'Подгр.' in group_text or 'подгр.' in group_text.lower():
                        match = re.search(r':\s*(.+)$', group_text)
                        if match:
                            groups.append(match.group(1).strip())
                    elif group_text and not any(x in group_text.lower() for x in ['аудитория', 'корпус']):
                        groups.append(group_text)
            
            # Determine specific_date for exams
            specific_date = None
            if lesson_type == 'экз' and subject_name in exam_dates:
                specific_date = exam_dates[subject_name].date()
            
            # Create lesson data for each group (or one if no groups found)
            if groups:
                result = []
                for group_name in groups:
                    result.append({
                        'subject_name': subject_name,
                        'group_name': group_name,
                        'lesson_type': lesson_type,
                        'room': room,
                        'weekday': weekday,
                        'lesson_number': lesson_number,
                        'start_time': start_time,
                        'end_time': end_time,
                        'specific_date': specific_date,
                        'week_number': None,
                    })
                return result
            else:
                # No group specified
                return {
                    'subject_name': subject_name,
                    'group_name': None,
                    'lesson_type': lesson_type,
                    'room': room,
                    'weekday': weekday,
                    'lesson_number': lesson_number,
                    'start_time': start_time,
                    'end_time': end_time,
                    'specific_date': specific_date,
                    'week_number': None,
                }
        except Exception as e:
            logger.error(f"Error parsing teacher lesson: {e}")
            return None

