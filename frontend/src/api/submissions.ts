import apiClient from '@/api/client'
import type { CandidateSubmission, OwnerDashboardClient } from '@/types/jobRequirement'

export async function submitCandidate(
  jobRequirementId: string,
  candidateId: string,
  submissionData: Record<string, string>,
): Promise<CandidateSubmission> {
  const { data } = await apiClient.post<CandidateSubmission>(
    `/api/v1/job-requirements/${jobRequirementId}/submissions`,
    { candidate_id: candidateId, submission_data: submissionData },
  )
  return data
}

export async function fetchSubmissions(jobRequirementId: string): Promise<CandidateSubmission[]> {
  const { data } = await apiClient.get<CandidateSubmission[]>(
    `/api/v1/job-requirements/${jobRequirementId}/submissions`,
  )
  return data
}

export async function approveSubmission(
  appId: string,
  action: 'approved' | 'rejected',
  remarks?: string,
): Promise<CandidateSubmission> {
  const { data } = await apiClient.patch<CandidateSubmission>(
    `/api/v1/submissions/${appId}/approve`,
    { action, remarks },
  )
  return data
}

async function parseBlobError(error: unknown): Promise<never> {
  const ax = error as {
    message?: string
    response?: { data?: Blob | { detail?: unknown }; status?: number }
  }
  const data = ax.response?.data
  if (data instanceof Blob) {
    try {
      const text = await data.text()
      const parsed = JSON.parse(text) as { detail?: unknown }
      const detail = parsed.detail
      if (typeof detail === 'string') {
        throw new Error(detail)
      }
      if (detail && typeof detail === 'object' && 'message' in detail) {
        throw new Error(String((detail as { message: unknown }).message))
      }
    } catch (e) {
      if (e instanceof Error && e.message !== 'Unexpected end of JSON input') {
        // Re-throw our parsed API errors; fall through for JSON parse failures
        if (!(e instanceof SyntaxError)) throw e
      }
    }
  }
  throw error instanceof Error ? error : new Error(ax.message ?? 'Download failed')
}

function triggerBlobDownload(data: Blob, filename: string): void {
  const url = URL.createObjectURL(
    new Blob([data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function filenameFromDisposition(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback
  const utfMatch = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1])
    } catch {
      /* ignore */
    }
  }
  const match = /filename="?([^";]+)"?/i.exec(disposition)
  return match?.[1]?.trim() || fallback
}

async function downloadExcel(url: string, fallbackFilename: string): Promise<void> {
  try {
    const { data, headers } = await apiClient.get<Blob>(url, {
      responseType: 'blob',
      headers: { Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
    })
    if (!(data instanceof Blob) || data.size === 0) {
      throw new Error('Download returned an empty file')
    }
    // Guard: server may return a JSON error body incorrectly typed as a blob
    if (data.type.includes('application/json')) {
      const text = await data.text()
      let message = 'Download failed'
      try {
        const parsed = JSON.parse(text) as { detail?: unknown }
        if (typeof parsed.detail === 'string') message = parsed.detail
      } catch {
        /* keep default message */
      }
      throw new Error(message)
    }
    const disposition = (headers['content-disposition'] ?? headers['Content-Disposition']) as
      | string
      | undefined
    triggerBlobDownload(data, filenameFromDisposition(disposition, fallbackFilename))
  } catch (err) {
    await parseBlobError(err)
  }
}

export async function downloadSubmission(appId: string, filename: string): Promise<void> {
  await downloadExcel(`/api/v1/submissions/${appId}/download`, filename)
}

export async function downloadAllSubmissions(jobRequirementId: string, filename: string): Promise<void> {
  await downloadExcel(
    `/api/v1/job-requirements/${jobRequirementId}/submissions/download-all`,
    filename,
  )
}

export async function downloadApprovedClientSubmissions(
  clientId: string,
  filename: string,
): Promise<void> {
  await downloadExcel(`/api/v1/submissions/owner/download-approved/${clientId}`, filename)
}

export async function fetchOwnerDashboard(): Promise<OwnerDashboardClient[]> {
  const { data } = await apiClient.get<OwnerDashboardClient[]>('/api/v1/submissions/owner/dashboard')
  return data
}
