import request from './index'

const institutionAPI = {
  info() {
    return request({ url: '/api/v1/institution/info', method: 'get' })
  },
  dashboard() {
    return request({ url: '/api/v1/institution/dashboard', method: 'get' })
  },
  students(status) {
    return request({ url: '/api/v1/institution/students', method: 'get', params: status ? { status } : {} })
  },
  approveStudent(userId) {
    return request({ url: `/api/v1/institution/students/${userId}/approve`, method: 'post' })
  },
  importStudents(students) {
    return request({ url: '/api/v1/institution/students/import', method: 'post', data: { students } })
  },
  assignAdvisor(studentUserId, advisorId) {
    return request({ url: '/api/v1/institution/advisor/assign', method: 'post', data: { student_user_id: studentUserId, advisor_id: advisorId } })
  },
  downloadReport() {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const token = localStorage.getItem('access_token')
    // 报表需带鉴权头，用 fetch 下载 blob
    return fetch(`${baseURL}/api/v1/institution/report.csv`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.blob()).then(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'institution_usage.csv'
      a.click()
      URL.revokeObjectURL(url)
    })
  },
}

export default institutionAPI
