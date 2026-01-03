import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { X, Upload as UploadIcon } from 'lucide-react'
import { formatFileSize } from '@/lib/utils'

interface MaterialUploadProps {
  branchId: number
  onClose: () => void
  onSuccess: () => void
}

export default function MaterialUpload({ branchId, onClose, onSuccess }: MaterialUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [fileComments, setFileComments] = useState<Record<number, string>>({})
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const queryClient = useQueryClient()

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      setFiles((prev) => [...prev, ...acceptedFiles])
    },
    multiple: true,
  })

  // Get input props and add id for label association
  const inputProps = getInputProps()
  const fileInputId = 'material-files-input'

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    const newComments = { ...fileComments }
    delete newComments[index]
    setFileComments(newComments)
  }

  const mutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post('/materials/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return res.data
    },
    onSuccess: () => {
      toast.success('Материал загружен и отправлен на модерацию')
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка загрузки материала')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (files.length === 0) {
      toast.error('Выберите хотя бы один файл')
      return
    }

    const formData = new FormData()
    formData.append('branch', branchId.toString())
    if (description) {
      formData.append('description', description)
    }
    
    files.forEach((file) => {
      formData.append('files', file)
    })
    
    Object.keys(fileComments).forEach((key) => {
      const index = parseInt(key)
      if (fileComments[index]) {
        formData.append(`file_comments[${index}]`, fileComments[index])
      }
    })

    if (tags) {
      tags.split(',').forEach((tag) => {
        const trimmedTag = tag.trim()
        if (trimmedTag) {
          formData.append('tags', trimmedTag)
        }
      })
    }

    mutation.mutate(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-card border rounded-lg p-6 w-full max-w-2xl my-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Загрузка материалов</h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="material-description" className="block text-sm font-medium mb-2">Описание</label>
            <textarea
              id="material-description"
              name="material-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              placeholder="Описание материалов..."
            />
          </div>

          <div>
            <label htmlFor="material-tags" className="block text-sm font-medium mb-2">Теги (через запятую)</label>
            <input
              id="material-tags"
              name="material-tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="лекции, практика, экзамен"
            />
          </div>

          <div>
            <label htmlFor={fileInputId} className="block text-sm font-medium mb-2">Файлы</label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
              }`}
            >
              <input {...inputProps} id={fileInputId} />
              <UploadIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {isDragActive
                  ? 'Отпустите файлы здесь'
                  : 'Перетащите файлы сюда или нажмите для выбора'}
              </p>
            </div>

            {files.length > 0 && (
              <div className="mt-4 space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-accent rounded">
                    <span className="flex-1 text-sm">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </span>
                    <label htmlFor={`file-comment-${index}`} className="sr-only">Комментарий к файлу {file.name}</label>
                    <input
                      id={`file-comment-${index}`}
                      name={`file-comment-${index}`}
                      type="text"
                      placeholder="Комментарий к файлу"
                      value={fileComments[index] || ''}
                      onChange={(e) =>
                        setFileComments({ ...fileComments, [index]: e.target.value })
                      }
                      className="flex-1 px-2 py-1 text-sm border rounded"
                    />
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="p-1 hover:bg-destructive/10 rounded"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-accent"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={mutation.isPending || files.length === 0}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {mutation.isPending ? 'Загрузка...' : 'Загрузить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

