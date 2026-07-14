import apiClient from '@/api/client'

export interface AttendanceRecord {
  date: string
  check_in: string | null
  check_out: string | null
  status: 'on_time' | 'late' | 'absent'
}

export interface RecruiterAttendanceRow {
  user_id: string
  first_name: string
  last_name: string
  employee_code: string | null
  designation: string | null
  check_in: string | null
  check_out: string | null
  status: 'on_time' | 'late' | 'absent'
}

export async function fetchMyToday(): Promise<AttendanceRecord> {
  const { data } = await apiClient.get<AttendanceRecord>('/api/v1/attendance/today/me')
  return data
}

export async function checkIn(): Promise<AttendanceRecord> {
  const { data } = await apiClient.post<AttendanceRecord>('/api/v1/attendance/checkin')
  return data
}

export async function checkOut(): Promise<AttendanceRecord> {
  const { data } = await apiClient.post<AttendanceRecord>('/api/v1/attendance/checkout')
  return data
}

export async function fetchAllToday(): Promise<RecruiterAttendanceRow[]> {
  const { data } = await apiClient.get<RecruiterAttendanceRow[]>('/api/v1/attendance/today')
  return data
}

export interface AttendancePolicy {
  checkin_expected: string
  checkout_expected: string
  late_threshold: string
  timezone: string
}

export async function fetchPolicy(): Promise<AttendancePolicy> {
  const { data } = await apiClient.get<AttendancePolicy>('/api/v1/attendance/policy')
  return data
}
