import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as attendanceApi from '@/api/attendance'
import type { AttendanceRecord, RecruiterAttendanceRow } from '@/api/attendance'

export { type AttendanceRecord, type RecruiterAttendanceRow }

export const useAttendanceStore = defineStore('attendance', () => {
  const myRecord = ref<AttendanceRecord | null>(null)
  const allRecords = ref<RecruiterAttendanceRow[]>([])
  const loading = ref(false)
  const allLoading = ref(false)
  const error = ref('')

  async function fetchMyToday() {
    loading.value = true
    error.value = ''
    try {
      myRecord.value = await attendanceApi.fetchMyToday()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load attendance'
    } finally {
      loading.value = false
    }
  }

  async function checkIn() {
    loading.value = true
    error.value = ''
    try {
      myRecord.value = await attendanceApi.checkIn()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Check-in failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function checkOut() {
    loading.value = true
    error.value = ''
    try {
      myRecord.value = await attendanceApi.checkOut()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Check-out failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAllToday() {
    allLoading.value = true
    try {
      allRecords.value = await attendanceApi.fetchAllToday()
    } catch {
      // silently fail for owner table
    } finally {
      allLoading.value = false
    }
  }

  return {
    myRecord,
    allRecords,
    loading,
    allLoading,
    error,
    fetchMyToday,
    checkIn,
    checkOut,
    fetchAllToday,
  }
})
