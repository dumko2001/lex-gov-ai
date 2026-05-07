import * as React from "react"
import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { useUploadJudgment } from "@/hooks/useJudgments"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, X, CheckCircle } from "lucide-react"
import { Link } from "@tanstack/react-router"

function UploadPage() {
  const [files, setFiles] = React.useState<File[]>([])
  const [uploadedCount, setUploadedCount] = React.useState(0)
  const [isDragging, setIsDragging] = React.useState(false)
  const uploadMutation = useUploadJudgment()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === 'application/pdf' || f.name.endsWith('.pdf')
    )
    setFiles((prev) => [...prev, ...droppedFiles])
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).filter(
        (f) => f.type === 'application/pdf' || f.name.endsWith('.pdf')
      )
      setFiles((prev) => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    let completed = 0
    for (const file of files) {
      await uploadMutation.mutateAsync(file)
      completed += 1
    }
    setUploadedCount((v) => v + completed)
    setFiles([])
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Upload Judgment</h2>
        <p className="text-slate-500">Upload court judgment PDFs. The system extracts directives and routes verified actions to dashboard.</p>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors
          ${isDragging 
            ? 'border-indigo-500 bg-indigo-50' 
            : 'border-slate-300 bg-white hover:bg-slate-50'
          }
        `}
      >
        <Upload className="mb-4 h-12 w-12 text-slate-400" />
        <p className="mb-2 text-lg font-medium text-slate-700">
          Drag and drop PDF files here
        </p>
        <p className="mb-4 text-sm text-slate-500">or click to browse</p>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileInput}
          className="hidden"
          id="file-input"
        />
        <label htmlFor="file-input">
          <Button variant="outline" className="cursor-pointer" asChild>
            <span>Select Files</span>
          </Button>
        </label>
      </div>

      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Files to Upload</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-md border bg-slate-50 p-3"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">{file.name}</p>
                    <p className="text-xs text-slate-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {uploadMutation.isSuccess && (
                    <Badge variant="success" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Done
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-red-600"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}

            <div className="flex justify-end pt-2">
              <Button
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                {uploadMutation.isPending ? 'Processing Upload...' : `Upload ${files.length} file(s)`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Operator Workflow</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3 text-sm">
            <Badge variant="outline">1</Badge>
            <p>Upload judgment PDF and wait for extraction to complete.</p>
          </div>
          <div className="flex items-start gap-3 text-sm">
            <Badge variant="outline">2</Badge>
            <p>Open Verification and approve/edit/redo each directive with source evidence.</p>
          </div>
          <div className="flex items-start gap-3 text-sm">
            <Badge variant="outline">3</Badge>
            <p>Publish verified directives to Department Dashboard and monitor alerts.</p>
          </div>
          <div className="flex items-center justify-between rounded-md border bg-slate-50 px-3 py-2">
            <span className="text-sm text-slate-700">Uploaded this session: {uploadedCount}</span>
            <div className="flex gap-2">
              <Link to="/dashboard"><Button size="sm" variant="outline">Go to Dashboard</Button></Link>
              <Link to="/alerts"><Button size="sm" variant="ghost">View Alerts</Button></Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/upload',
  component: UploadPage,
})
