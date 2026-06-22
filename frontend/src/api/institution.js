import request from './index'

const institutionAPI = {
  // 学生用机构邀请码自助注册（公开，需后续管理员审批）
  registerStudent(payload) {
    return request({ url: '/api/v1/institution/register-student', method: 'post', data: payload })
  },
  // 系统管理员：创建机构
  create(payload) {
    return request({ url: '/api/v1/institution/create', method: 'post', data: payload })
  },
  // 系统管理员：所有机构列表
  list() {
    return request({ url: '/api/v1/institution/list', method: 'get' })
  },
  // 以下接口：机构管理员不传 instId（用自己机构）；系统管理员传 instId 查看指定机构
  info(instId) {
    return request({ url: '/api/v1/institution/info', method: 'get', params: instId ? { institution_id: instId } : {} })
  },
  dashboard(instId) {
    return request({ url: '/api/v1/institution/dashboard', method: 'get', params: instId ? { institution_id: instId } : {} })
  },
  students(status, instId) {
    const params = {}
    if (status) params.status = status
    if (instId) params.institution_id = instId
    return request({ url: '/api/v1/institution/students', method: 'get', params })
  },
  approveStudent(userId, instId) {
    return request({ url: `/api/v1/institution/students/${userId}/approve`, method: 'post', params: instId ? { institution_id: instId } : {} })
  },
  importStudents(students) {
    return request({ url: '/api/v1/institution/students/import', method: 'post', data: { students } })
  },
  assignAdvisor(studentUserId, advisorId) {
    return request({ url: '/api/v1/institution/advisor/assign', method: 'post', data: { student_user_id: studentUserId, advisor_id: advisorId } })
  },
  downloadReport(instId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const token = localStorage.getItem('access_token')
    const q = instId ? `?institution_id=${instId}` : ''
    // 报表需带鉴权头，用 fetch 下载 blob
    return fetch(`${baseURL}/api/v1/institution/report.csv${q}`, {
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
