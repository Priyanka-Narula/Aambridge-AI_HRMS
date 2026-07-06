export interface SubmissionField {
  field: string
  type: string
  required: boolean
}

export interface ClientContactItem {
  id?: string
  name: string
  designation?: string | null
  email?: string | null
  phone?: string | null
  linkedin_url?: string | null
  primary_contact: boolean
}

export interface ClientListItem {
  id: string
  company_name: string
  industry?: string | null
  location?: string | null
  website?: string | null
  company_size?: string | null
  billing_address?: string | null
  gst_number?: string | null
  payment_terms?: string | null
  portal_url?: string | null
  status: string
  submission_format?: SubmissionField[] | null
  contacts: ClientContactItem[]
  created_at?: string | null
}

export interface ClientCreatePayload {
  company_name: string
  industry?: string | null
  location?: string | null
  website?: string | null
  company_size?: string | null
  billing_address?: string | null
  gst_number?: string | null
  payment_terms?: string | null
  portal_url?: string | null
  submission_format?: SubmissionField[] | null
  contacts: ClientContactItem[]
}

export interface ClientUpdatePayload extends ClientCreatePayload {}
