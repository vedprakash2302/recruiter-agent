import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function POST(request) {
  try {
    const formData = await request.formData()
    const file = formData.get('resume')
    const jobUrl = formData.get('jobUrl')

    if (!file) {
      return NextResponse.json(
        { error: 'No file received' },
        { status: 400 }
      )
    }

    if (!jobUrl) {
      return NextResponse.json(
        { error: 'Job URL is required' },
        { status: 400 }
      )
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
      return NextResponse.json(
        { error: 'Only PDF files are allowed' },
        { status: 400 }
      )
    }

    // Create resumes directory if it doesn't exist
    const resumesDir = path.join(process.cwd(), '..', 'resumes')
    if (!existsSync(resumesDir)) {
      await mkdir(resumesDir, { recursive: true })
    }

    // Generate unique filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const originalName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_')
    const filename = `${timestamp}_${originalName}`
    const filepath = path.join(resumesDir, filename)

    // Save file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filepath, buffer)

    // Call FastAPI main.py tool with the required parameters
    try {
      const fastApiResponse = await fetch('http://localhost:8000/api/process-resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: jobUrl,
          filename: filename
        })
      })

      let fastApiResult = {}
      if (fastApiResponse.ok) {
        fastApiResult = await fastApiResponse.json()
      } else {
        console.warn('FastAPI call failed:', fastApiResponse.status, fastApiResponse.statusText)
        // Continue anyway - file was uploaded successfully
      }

      return NextResponse.json({
        success: true,
        message: 'Resume uploaded successfully',
        filename: filename,
        jobUrl: jobUrl,
        fastApiResult: fastApiResult
      })

    } catch (fastApiError) {
      console.warn('FastAPI integration error:', fastApiError)
      // Return success anyway since file upload worked
      return NextResponse.json({
        success: true,
        message: 'Resume uploaded successfully (FastAPI integration pending)',
        filename: filename,
        jobUrl: jobUrl,
        warning: 'Backend processing service unavailable'
      })
    }

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: 'Upload failed: ' + error.message },
      { status: 500 }
    )
  }
}

export async function GET() {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  )
}