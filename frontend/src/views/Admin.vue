<template>
  <div class="modern-page-container">
    <div class="admin-header">
      <h2>管理员后台</h2>
      <el-tag type="warning">系统管理</el-tag>
      <div style="flex: 1" />
    </div>

    <el-tabs v-model="activeTab" class="admin-tabs">
      <!-- 用户管理 Tab -->
      <el-tab-pane name="users">
        <template #label>
          <span>👤 用户管理</span>
        </template>

        <div style="margin-bottom: 20px;">
          <el-button type="primary" @click="showCreate = true">+ 新建用户</el-button>
        </div>

        <!-- 统计 -->
        <div class="admin-stats">
          <div class="stat-card">
            <div class="stat-num">{{ users.length }}</div>
            <div class="stat-label">总用户</div>
          </div>
          <div class="stat-card approved">
            <div class="stat-num">{{ activeUsersCount }}</div>
            <div class="stat-label">活跃用户（近7天）</div>
          </div>
        </div>

        <!-- 全部用户 -->
        <el-card class="admin-card">
          <template #header>全部用户</template>
          <el-table :data="users" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column label="注册方式" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.phone" type="success" size="small">📱 手机号</el-tag>
                <el-tag v-else-if="row.wechat_openid" type="primary" size="small">💬 微信</el-tag>
                <el-tag v-else type="info" size="small">👤 账号</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="联系方式" min-width="140">
              <template #default="{ row }">
                <div v-if="row.phone" style="font-size: 12px; color: #666;">{{ maskPhone(row.phone) }}</div>
                <div v-else-if="row.nickname" style="font-size: 12px; color: #666;">{{ row.nickname }}</div>
                <div v-else-if="row.email" style="font-size: 12px; color: #666;">{{ row.email }}</div>
                <span v-else style="color: #999; font-size: 12px;">未填写</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_admin" type="danger">管理员</el-tag>
                <el-tag v-else-if="row.is_active" type="success">正常</el-tag>
                <el-tag v-else type="info">已禁用</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="剩余额度" width="100">
              <template #default="{ row }">
                <span v-if="row.is_admin" style="color: #999; font-size: 12px;">无限制</span>
                <span v-else>{{ row.total_credits ?? 0 }} 次</span>
              </template>
            </el-table-column>
            <el-table-column label="注册时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="showGrantQuotaDialog(row)">
                  赠送额度
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

      </el-tab-pane>

      <!-- 充值管理 Tab -->
      <el-tab-pane name="billing">
        <template #label>
          <span>💳 充值管理</span>
        </template>

        <!-- 订单统计 -->
        <div class="admin-stats">
          <div class="stat-card">
            <div class="stat-num">{{ orders.length }}</div>
            <div class="stat-label">总订单数</div>
          </div>
          <div class="stat-card paid">
            <div class="stat-num">{{ paidOrdersCount }}</div>
            <div class="stat-label">已支付</div>
          </div>
          <div class="stat-card pending">
            <div class="stat-num">{{ pendingOrdersCount }}</div>
            <div class="stat-label">待支付</div>
          </div>
          <div class="stat-card" style="border-top-color: #ff9800;">
            <div class="stat-num">{{ refundPendingCount }}</div>
            <div class="stat-label">待审核退款</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">¥{{ totalRevenue.toFixed(2) }}</div>
            <div class="stat-label">总收入</div>
          </div>
        </div>

        <!-- 退款申请审核 -->
        <el-card class="admin-card" style="margin-bottom: 20px;">
          <template #header>
            <span>📋 退款申请审核</span>
            <el-badge :value="refundPendingCount" type="warning" style="margin-left: 8px;" />
          </template>

          <el-table :data="refundRequests" stripe v-if="refundRequests.length > 0">
            <el-table-column prop="order_no" label="订单号" width="180" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column label="金额" width="100">
              <template #default="{ row }">
                ¥{{ (row.amount_cents / 100).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="退款原因" min-width="200">
              <template #default="{ row }">
                {{ row.refund_reason }}
              </template>
            </el-table-column>
            <el-table-column label="申请时间" width="160">
              <template #default="{ row }">{{ formatDate(row.refund_applied_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button type="success" size="small" @click="showApproveDialog(row)">
                  通过
                </el-button>
                <el-button type="danger" size="small" @click="showRejectDialog(row.order_no)">
                  拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-else description="暂无待审核的退款申请"></el-empty>
        </el-card>

        <!-- 订单列表卡片 -->
        <el-card class="admin-card" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>订单管理</span>
              <el-select v-model="orderStatusFilter" placeholder="按状态筛选" style="width: 150px; margin-left: 20px;">
                <el-option label="全部" value="" />
                <el-option label="待支付" value="pending" />
                <el-option label="已支付" value="paid" />
                <el-option label="待处理" value="refund_pending" />
                <el-option label="已退款" value="refunded" />
              </el-select>
            </div>
          </template>

          <el-table :data="pagedOrders" stripe>
            <el-table-column prop="order_no" label="订单号" width="180" />
            <el-table-column prop="user_id" label="用户ID" width="80" />
            <el-table-column label="套餐类型" width="120">
              <template #default="{ row }">
                {{ row.product_type === 'monthly' ? '包月订阅' : `按次购买(${row.quantity}次)` }}
              </template>
            </el-table-column>
            <el-table-column label="金额" width="100">
              <template #default="{ row }">
                ¥{{ (row.amount_cents / 100).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="支付方式" width="100">
              <template #default="{ row }">
                {{ row.pay_method === 'wechat' ? '微信' : row.pay_method === 'alipay' ? '支付宝' : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'paid'" type="success">已支付</el-tag>
                <el-tag v-else-if="row.status === 'pending'" type="warning">待支付</el-tag>
                <el-tag v-else-if="row.status === 'refund_pending'" type="danger">待处理</el-tag>
                <el-tag v-else-if="row.status === 'refunded'" type="info">已退款</el-tag>
                <el-tag v-else>{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="下单时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button v-if="row.status === 'paid'" type="danger" size="small" @click="handleRefund(row.order_no)">
                  退款
                </el-button>
                <span v-else style="color: #999; font-size: 12px;">-</span>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-if="filteredOrders.length > orderPageSize"
            v-model:current-page="orderPage"
            :page-size="orderPageSize"
            :total="filteredOrders.length"
            layout="prev, pager, next"
            class="order-pagination"
          />
        </el-card>

      </el-tab-pane>

      <!-- 论文库 Tab -->
      <el-tab-pane name="papers">
        <template #label><span>📚 论文库</span></template>

        <!-- 统计卡片 -->
        <div class="admin-stats" style="grid-template-columns: repeat(5,1fr); display:grid; gap:16px; margin-bottom:20px;">
          <div class="stat-card">
            <div class="stat-num">{{ paperStats.total?.toLocaleString() ?? '—' }}</div>
            <div class="stat-label">收录总量（篇）</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ paperStats.index_size_mb ? paperStats.index_size_mb.toFixed(0) + ' MB' : '—' }}</div>
            <div class="stat-label">FAISS 索引大小</div>
          </div>
          <div class="stat-card pending">
            <div class="stat-num">+{{ paperStats.today_writeback ?? 0 }}</div>
            <div class="stat-label">今日自动写回</div>
          </div>
          <div class="stat-card" :class="paperStats.index_ready ? 'approved' : 'pending'">
            <div class="stat-num" style="font-size:20px; padding-top:6px">
              {{ paperStats.index_ready ? '✅ 就绪' : '⚠️ 未就绪' }}
            </div>
            <div class="stat-label">索引状态</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="font-size:20px; padding-top:6px">
              {{ paperStats.index_total?.toLocaleString() ?? '—' }}
            </div>
            <div class="stat-label">索引向量数</div>
          </div>
        </div>

        <!-- 来源分布 -->
        <el-card class="admin-card" style="margin-bottom:16px;" v-if="paperStats.by_source?.length">
          <template #header><span style="font-weight:600">来源分布</span></template>
          <div v-for="s in paperStats.by_source" :key="s.source" style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
            <span style="width:160px;font-size:13px;color:#606266;">{{ s.source }}</span>
            <el-progress
              :percentage="paperStats.total ? Math.round(s.count / paperStats.total * 100) : 0"
              :stroke-width="14"
              style="flex:1"
              :color="s.source === 'openalex' ? '#006C49' : '#409eff'"
            />
            <span style="width:100px;text-align:right;font-size:13px;color:#909399;">{{ s.count.toLocaleString() }} 篇</span>
          </div>
        </el-card>

        <!-- 操作栏 -->
        <el-card class="admin-card" style="margin-bottom:16px;">
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <el-input
              v-model="paperSearch.keyword"
              placeholder="搜索标题 / DOI / 作者"
              clearable style="width:260px;"
              @keyup.enter="loadPapers(1)"
            />
            <el-select v-model="paperSearch.source" placeholder="全部来源" clearable style="width:130px;">
              <el-option label="openalex" value="openalex" />
              <el-option label="external" value="external" />
              <el-option label="semantic_scholar" value="semantic_scholar" />
            </el-select>
            <el-input-number v-model="paperSearch.year_from" :min="1900" :max="2030" placeholder="起始年" style="width:110px;" controls-position="right" :value-on-clear="null" />
            <span style="color:#c0c4cc">—</span>
            <el-input-number v-model="paperSearch.year_to" :min="1900" :max="2030" placeholder="截止年" style="width:110px;" controls-position="right" :value-on-clear="null" />
            <el-select v-model="paperSearch.has_embedding" placeholder="有无向量" clearable style="width:110px;">
              <el-option label="有向量" :value="true" />
              <el-option label="无向量" :value="false" />
            </el-select>
            <el-button type="primary" @click="loadPapers(1)">搜索</el-button>
            <el-button @click="resetPaperSearch">重置</el-button>
            <div style="flex:1" />
            <el-button type="success" :loading="rebuilding" @click="handleRebuild">⚙️ 重建索引</el-button>
            <el-button @click="loadPaperStats(); loadPapers(1)">🔄 刷新</el-button>
          </div>
          <div v-if="rebuilding" style="margin-top:12px;">
            <el-progress :percentage="rebuildProgress" :stroke-width="10" :striped="true" :striped-flow="true" :duration="10" />
            <div style="font-size:12px;color:#909399;margin-top:4px;">{{ rebuildMsg }}</div>
          </div>
        </el-card>

        <!-- 论文列表 -->
        <el-card class="admin-card">
          <el-table :data="papers" stripe v-loading="papersLoading" style="width:100%">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column label="标题" min-width="280">
              <template #default="{ row }">
                <el-tooltip :content="row.title" placement="top" :show-after="400">
                  <span style="cursor:pointer;color:#303133;font-weight:500;" @click="openPaperDetail(row.id)">
                    {{ row.title?.length > 55 ? row.title.slice(0, 55) + '…' : row.title }}
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="作者" width="150">
              <template #default="{ row }">
                <span style="font-size:12px;color:#606266;">{{ row.authors?.split(';')[0] || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="year" label="年份" width="70" align="center" />
            <el-table-column label="来源" width="120">
              <template #default="{ row }">
                <el-tag :type="row.source === 'openalex' ? 'success' : row.source === 'external' ? 'primary' : 'warning'" size="small">
                  {{ row.source }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="向量" width="65" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.has_embedding ? '#67c23a' : '#c0c4cc' }">
                  {{ row.has_embedding ? '✓' : '—' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="入库时间" width="140" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openPaperDetail(row.id)">详情</el-button>
                <el-button size="small" type="danger" @click="handleDeletePaper(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-if="paperTotal > paperPageSize"
            v-model:current-page="paperPage"
            :page-size="paperPageSize"
            :total="paperTotal"
            layout="total, sizes, prev, pager, next"
            :page-sizes="[20, 50, 100]"
            @current-change="loadPapers"
            @size-change="(s) => { paperPageSize = s; loadPapers(1) }"
            style="margin-top:16px;justify-content:center;"
          />
        </el-card>
      </el-tab-pane>

      <!-- 机构管理 Tab（B端） -->
      <el-tab-pane name="institutions">
        <template #label><span>🏫 机构管理</span></template>

        <div style="margin-bottom: 20px;">
          <el-button type="primary" @click="showCreateInst = true">+ 新建机构</el-button>
          <span class="inst-hint">建机构时指派的「管理员账号 ID」，将自动成为该机构管理员，登录后在头像菜单可见「机构管理」控制台。</span>
        </div>

        <el-card class="admin-card">
          <template #header>全部机构</template>
          <el-table :data="institutions" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="机构名称" min-width="140" />
            <el-table-column label="规模" width="90">
              <template #default="{ row }">{{ instLevelLabel(row.subscription_level) }}</template>
            </el-table-column>
            <el-table-column label="配额" width="140">
              <template #default="{ row }">{{ row.quota_used }} / {{ row.quota_total }}（剩 {{ row.quota_remaining }}）</template>
            </el-table-column>
            <el-table-column prop="student_count" label="学生数" width="80" />
            <el-table-column label="邀请码" width="120">
              <template #default="{ row }">
                <el-tag type="success" size="small" style="cursor:pointer" @click="copyText(row.invite_code)">{{ row.invite_code }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="管理员" min-width="120">
              <template #default="{ row }">
                <span v-if="row.admins && row.admins.length">
                  {{ row.admins.map(a => a.username + '(#' + a.id + ')').join(', ') }}
                </span>
                <span v-else style="color:#999;font-size:12px;">未指派</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
                <el-tag v-else type="info" size="small">停用</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="enterConsole(row)">进入控制台</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建机构弹窗 -->
    <el-dialog v-model="showCreateInst" title="新建机构" width="480px">
      <el-form label-width="120px">
        <el-form-item label="机构名称" required>
          <el-input v-model="instForm.name" placeholder="如：浙江大学" />
        </el-form-item>
        <el-form-item label="校域名（可选）">
          <el-input v-model="instForm.domain" placeholder="如：zju.edu.cn" />
        </el-form-item>
        <el-form-item label="规模">
          <el-select v-model="instForm.subscription_level" style="width:100%">
            <el-option label="小规模（<100 学生）" value="small" />
            <el-option label="中规模（100-500）" value="medium" />
            <el-option label="大规模（>500）" value="large" />
          </el-select>
        </el-form-item>
        <el-form-item label="配额池总额">
          <el-input-number v-model="instForm.quota_total" :min="0" :step="100" />
          <span class="inst-hint">机构学生共用，单位 credit</span>
        </el-form-item>
        <el-form-item label="管理员用户名">
          <el-input v-model="instForm.admin_username" placeholder="如：zju_admin" />
          <span class="inst-hint">账号不存在则按下方密码当场创建并设为管理员；已存在则直接提升</span>
        </el-form-item>
        <el-form-item label="管理员密码">
          <el-input v-model="instForm.admin_password" placeholder="新建账号时使用（≥6位）；提升已有账号可留空" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateInst = false">取消</el-button>
        <el-button type="primary" :loading="instCreating" @click="handleCreateInst">创建</el-button>
      </template>
    </el-dialog>

    <!-- 论文详情弹窗 -->
    <el-dialog v-model="showPaperDetail" title="论文详情" width="660px" :close-on-click-modal="true">
      <div v-if="currentPaper" style="line-height:1.8;">
        <div style="font-size:16px;font-weight:600;color:#303133;margin-bottom:16px;">{{ currentPaper.title }}</div>
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
          <el-descriptions-item label="DOI">
            <el-link v-if="currentPaper.doi" :href="`https://doi.org/${currentPaper.doi}`" target="_blank" type="primary">{{ currentPaper.doi }}</el-link>
            <span v-else style="color:#c0c4cc">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="年份">{{ currentPaper.year ?? '—' }}</el-descriptions-item>
          <el-descriptions-item label="作者" :span="2">{{ currentPaper.authors || '—' }}</el-descriptions-item>
          <el-descriptions-item label="来源">
            <el-tag size="small" :type="currentPaper.source === 'openalex' ? 'success' : 'primary'">{{ currentPaper.source }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="向量维度">{{ currentPaper.embedding_dim ? currentPaper.embedding_dim + ' 维 ✓' : '无向量' }}</el-descriptions-item>
          <el-descriptions-item label="入库时间" :span="2">{{ currentPaper.created_at }}</el-descriptions-item>
        </el-descriptions>
        <div style="font-size:13px;color:#909399;margin-bottom:6px;">摘要</div>
        <div style="background:#f5f7fa;border-radius:8px;padding:12px 14px;font-size:13px;color:#303133;line-height:1.7;max-height:220px;overflow-y:auto;">
          {{ currentPaper.abstract || '无摘要' }}
        </div>
      </div>
      <template #footer>
        <el-button type="danger" @click="handleDeletePaper(currentPaper); showPaperDetail = false">删除此论文</el-button>
        <el-button @click="showPaperDetail = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 新建用户弹窗 -->
    <el-dialog v-model="showCreate" title="新建用户" width="400px" :close-on-click-modal="false">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" placeholder="11位手机号" />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="createForm.is_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 赠送额度弹窗 -->
    <el-dialog v-model="showGrantDialog" title="赠送额度" width="400px" :close-on-click-modal="false">
      <el-form v-if="currentGrantUser" :model="grantForm" :rules="grantRules" ref="grantFormRef" label-width="80px">
        <el-form-item label="用户">
          <span>{{ currentGrantUser.username }}</span>
        </el-form-item>
        <el-form-item label="类型" prop="source">
          <el-radio-group v-model="grantForm.source">
            <el-radio value="free">免费试用次数</el-radio>
            <el-radio value="purchase">购买次数</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="赠送次数" prop="count">
          <el-input-number v-model.number="grantForm.count" :min="1" :max="100" :precision="0" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGrantDialog = false">取消</el-button>
        <el-button type="primary" :loading="grantingLoading" @click="handleGrantQuota">赠送</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝退款弹窗 -->
    <el-dialog v-model="showRejectRefundDialog" title="拒绝退款" width="400px" :close-on-click-modal="false">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="订单号">
          <span>{{ currentRejectOrderNo }}</span>
        </el-form-item>
        <el-form-item label="拒绝原因" prop="reason">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            placeholder="请说明拒绝原因"
            :rows="4"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectRefundDialog = false">取消</el-button>
        <el-button type="primary" :loading="rejectingLoading" @click="handleRejectRefund">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 批准退款弹窗（支持编辑退款金额） -->
    <el-dialog v-model="showApproveRefundDialog" title="批准退款" width="420px" :close-on-click-modal="false">
      <el-form :model="approveForm" :rules="approveRules" ref="approveFormRef" label-width="100px">
        <el-form-item label="订单号">
          <span style="font-family:monospace;">{{ approveForm.orderNo }}</span>
        </el-form-item>
        <el-form-item label="订单金额">
          <span>¥{{ approveForm.orderAmountYuan }}</span>
        </el-form-item>
        <el-form-item label="退款金额" prop="refundAmountYuan">
          <el-input
            v-model="approveForm.refundAmountYuan"
            placeholder="请输入退款金额"
            style="width:160px;"
          >
            <template #prepend>¥</template>
          </el-input>
          <span style="margin-left:8px;color:#999;font-size:12px;">最大 ¥{{ approveForm.orderAmountYuan }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveRefundDialog = false">取消</el-button>
        <el-button type="success" :loading="approvingLoading" @click="handleApproveRefundConfirm">确认退款</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import * as adminApi from '@/api/admin'
import institutionAPI from '@/api/institution'

const router = useRouter()
const authStore = useAuthStore()

// 用户管理
const users = ref([])
const showCreate = ref(false)
const creating = ref(false)
const createFormRef = ref()
const createForm = ref({ phone: '', is_admin: false })

// 机构管理（B端）
const institutions = ref([])
const showCreateInst = ref(false)
const instCreating = ref(false)
const instForm = ref({ name: '', domain: '', subscription_level: 'small', quota_total: 1000, admin_username: '', admin_password: '' })

// 充值管理
const activeTab = ref('users')
const orders = ref([])
const refundRequests = ref([])
const orderStatusFilter = ref('')
const userSearchKeyword = ref('')
const userQuotaList = ref([])
const showGrantDialog = ref(false)
const grantingLoading = ref(false)
const grantFormRef = ref()
const currentGrantUser = ref(null)
const grantForm = ref({ count: 1, source: 'free' })
const grantRules = {
  source: [{ required: true, message: '请选择类型', trigger: 'change' }],
  count: [
    { required: true, message: '请输入赠送次数', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '赠送次数需在1-100之间', trigger: 'blur' },
  ],
}

// 批准退款
const showApproveRefundDialog = ref(false)
const approvingLoading = ref(false)
const approveFormRef = ref()
const approveForm = ref({ orderNo: '', orderAmountYuan: '0.00', refundAmountYuan: '0.00' })
const approveRules = {
  refundAmountYuan: [
    { required: true, message: '请输入退款金额', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        const num = parseFloat(value)
        if (isNaN(num) || !/^\d+(\.\d{1,2})?$/.test(String(value).trim())) {
          return callback(new Error('请输入有效金额（最多两位小数）'))
        }
        if (num < 0.01) return callback(new Error('退款金额不能低于 ¥0.01'))
        if (num > parseFloat(approveForm.value.orderAmountYuan)) {
          return callback(new Error(`退款金额不能超过订单金额 ¥${approveForm.value.orderAmountYuan}`))
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

function showApproveDialog(row) {
  approveForm.value = {
    orderNo: row.order_no,
    orderAmountYuan: (row.amount_cents / 100).toFixed(2),
    refundAmountYuan: (row.amount_cents / 100).toFixed(2),
  }
  showApproveRefundDialog.value = true
}

async function handleApproveRefundConfirm() {
  try {
    await approveFormRef.value?.validate()
  } catch {
    return
  }
  approvingLoading.value = true
  try {
    const cents = Math.round(parseFloat(approveForm.value.refundAmountYuan) * 100)
    await adminApi.approveRefund(approveForm.value.orderNo, cents)
    ElMessage.success('退款已批准')
    showApproveRefundDialog.value = false
    loadRefundRequests()
    loadOrders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    approvingLoading.value = false
  }
}

// 拒绝退款
const showRejectRefundDialog = ref(false)
const rejectingLoading = ref(false)
const rejectFormRef = ref()
const currentRejectOrderNo = ref('')
const rejectForm = ref({ reason: '' })
const rejectRules = {
  reason: [
    { required: true, message: '请输入拒绝原因', trigger: 'blur' },
  ],
}

const createRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
}

const activeUsersCount = ref(0)

async function loadActiveUsersCount() {
  try {
    const res = await adminApi.getActiveUsersCount()
    activeUsersCount.value = res.data.count
  } catch {
    // 静默失败，保持0
  }
}

// 订单相关计算
const filteredOrders = computed(() => {
  if (!orderStatusFilter.value) return orders.value
  return orders.value.filter(o => o.status === orderStatusFilter.value)
})

const orderPage = ref(1)
const orderPageSize = 10
watch(orderStatusFilter, () => { orderPage.value = 1 })
const pagedOrders = computed(() => {
  const start = (orderPage.value - 1) * orderPageSize
  return filteredOrders.value.slice(start, start + orderPageSize)
})

const paidOrdersCount = computed(() => orders.value.filter(o => o.status === 'paid').length)
const pendingOrdersCount = computed(() => orders.value.filter(o => o.status === 'pending').length)
const refundPendingCount = computed(() => refundRequests.value.length)
const totalRevenue = computed(() => {
  return orders.value
    .filter(o => o.status === 'paid')
    .reduce((sum, o) => sum + o.amount_cents, 0) / 100
})

async function handleCreate() {
  await createFormRef.value?.validate()
  creating.value = true
  try {
    await adminApi.createUser(createForm.value)
    ElMessage.success('用户创建成功')
    showCreate.value = false
    createForm.value = { phone: '', is_admin: false }
    loadUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function loadUsers() {
  try {
    const res = await adminApi.listUsers()
    users.value = res.data
  } catch (e) {
    console.error('加载用户列表失败:', e)
    ElMessage.error('加载用户列表失败')
  }
}

function formatDate(dt) {
  return new Date(dt).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function maskPhone(phone) {
  if (!phone || phone.length !== 11) return phone
  return phone.substring(0, 3) + '****' + phone.substring(7)
}

async function loadOrders() {
  try {
    const res = await adminApi.listOrders()
    orders.value = res.data
  } catch {
    ElMessage.error('加载订单失败')
  }
}

async function loadUserQuotaList() {
  try {
    const res = await adminApi.listUsers(userSearchKeyword.value || undefined)
    userQuotaList.value = res.data
  } catch {
    ElMessage.error('加载用户列表失败')
  }
}

function showGrantQuotaDialog(user) {
  currentGrantUser.value = user
  grantForm.value = { count: 1, source: 'free' }
  showGrantDialog.value = true
}

async function handleGrantQuota() {
  await grantFormRef.value?.validate()
  grantingLoading.value = true
  try {
    await adminApi.grantQuota(currentGrantUser.value.id, grantForm.value.count, grantForm.value.source)
    const label = grantForm.value.source === 'free' ? '免费试用次数' : '购买次数'
    ElMessage.success(`已赠送 ${currentGrantUser.value.username} ${grantForm.value.count} 次${label}`)
    showGrantDialog.value = false
    loadUserQuotaList()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '赠送失败')
  } finally {
    grantingLoading.value = false
  }
}

async function handleRefund(orderNo) {
  await ElMessageBox.confirm('确定要退款吗？', '提示', { type: 'warning' })
  try {
    await adminApi.refundOrder(orderNo)
    ElMessage.success('退款成功')
    loadOrders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '退款失败')
  }
}

async function loadRefundRequests() {
  try {
    const res = await adminApi.listRefundRequests()
    refundRequests.value = res.data || []
  } catch (e) {
    console.error('加载退款申请失败:', e)
    ElMessage.error(e.response?.data?.detail || '加载退款申请失败')
  }
}


function showRejectDialog(orderNo) {
  currentRejectOrderNo.value = orderNo
  rejectForm.value = { reason: '' }
  showRejectRefundDialog.value = true
}

async function handleRejectRefund() {
  await rejectFormRef.value?.validate()
  rejectingLoading.value = true
  try {
    await adminApi.rejectRefund(currentRejectOrderNo.value, rejectForm.value.reason)
    ElMessage.success('退款申请已拒绝')
    showRejectRefundDialog.value = false
    loadRefundRequests()
    loadOrders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    rejectingLoading.value = false
  }
}

// ── 论文库 ────────────────────────────────────────────────────
const paperStats = ref({})
const papers = ref([])
const paperTotal = ref(0)
const paperPage = ref(1)
const paperPageSize = ref(20)
const papersLoading = ref(false)
const rebuilding = ref(false)
const rebuildProgress = ref(0)
const rebuildMsg = ref('')
const showPaperDetail = ref(false)
const currentPaper = ref(null)
const paperSearch = ref({
  keyword: '',
  source: '',
  year_from: null,
  year_to: null,
  has_embedding: null,
})

async function loadPaperStats() {
  try {
    const res = await adminApi.getPaperStats()
    paperStats.value = res.data
  } catch { /* 静默 */ }
}

async function loadPapers(page = paperPage.value) {
  papersLoading.value = true
  try {
    const params = {
      page,
      page_size: paperPageSize.value,
      ...Object.fromEntries(
        Object.entries(paperSearch.value).filter(([, v]) => v !== '' && v !== null && v !== undefined)
      ),
    }
    const res = await adminApi.listPapers(params)
    papers.value = res.data.items
    paperTotal.value = res.data.total
    paperPage.value = res.data.page
  } catch {
    ElMessage.error('加载论文列表失败')
  } finally {
    papersLoading.value = false
  }
}

function resetPaperSearch() {
  paperSearch.value = { keyword: '', source: '', year_from: null, year_to: null, has_embedding: null }
  loadPapers(1)
}

async function openPaperDetail(id) {
  try {
    const res = await adminApi.getPaperDetail(id)
    currentPaper.value = res.data
    showPaperDetail.value = true
  } catch {
    ElMessage.error('加载详情失败')
  }
}

async function handleDeletePaper(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title?.slice(0, 30)}…」？此操作不可恢复。`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await adminApi.deletePaper(row.id)
    ElMessage.success('已删除')
    loadPapers()
    loadPaperStats()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function handleRebuild() {
  try {
    await ElMessageBox.confirm('重建索引期间查重功能不受影响（旧索引仍可用），确认继续？', '重建 FAISS 索引', { type: 'warning' })
  } catch { return }
  rebuilding.value = true
  rebuildProgress.value = 10
  rebuildMsg.value = '正在重建，请稍候...'
  // 模拟进度（实际是同步阻塞接口）
  const timer = setInterval(() => {
    if (rebuildProgress.value < 85) rebuildProgress.value += Math.random() * 8
  }, 800)
  try {
    const res = await adminApi.rebuildIndex()
    clearInterval(timer)
    rebuildProgress.value = 100
    rebuildMsg.value = res.data.message
    ElMessage.success(res.data.message)
    await loadPaperStats()
  } catch (e) {
    clearInterval(timer)
    ElMessage.error(e.response?.data?.detail || '重建失败')
  } finally {
    setTimeout(() => { rebuilding.value = false; rebuildProgress.value = 0 }, 2000)
  }
}

// ── 机构管理 ──────────────────────────────────────────────
const instLevelMap = { small: '小规模', medium: '中规模', large: '大规模' }
function instLevelLabel(v) { return instLevelMap[v] || v || '—' }

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制邀请码：' + text)
  } catch {
    ElMessage.info('邀请码：' + text)
  }
}

function enterConsole(row) {
  router.push({ path: '/institution', query: { id: row.id } })
}

async function loadInstitutions() {
  try {
    const res = await institutionAPI.list()
    institutions.value = res.institutions || []
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载机构列表失败')
  }
}

async function handleCreateInst() {
  if (!instForm.value.name.trim()) {
    ElMessage.warning('请填写机构名称')
    return
  }
  instCreating.value = true
  try {
    const payload = {
      name: instForm.value.name.trim(),
      domain: instForm.value.domain.trim(),
      subscription_level: instForm.value.subscription_level,
      quota_total: instForm.value.quota_total,
      admin_username: instForm.value.admin_username.trim(),
      admin_password: instForm.value.admin_password,
    }
    const res = await institutionAPI.create(payload)
    const a = res.admin
    let msg = `机构「${res.name}」已创建，邀请码：${res.invite_code}`
    if (a) {
      msg += a.created
        ? `；管理员账号「${a.username}」已创建，请把账号密码交给对方登录`
        : `；已将「${a.username}」设为机构管理员`
    }
    ElMessageBox.alert(msg, '创建成功', { confirmButtonText: '知道了' })
    showCreateInst.value = false
    instForm.value = { name: '', domain: '', subscription_level: 'small', quota_total: 1000, admin_username: '', admin_password: '' }
    await loadInstitutions()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建机构失败')
  } finally {
    instCreating.value = false
  }
}

// 切换 tab 时自动加载
watch(activeTab, (val) => {
  if (val === 'papers') {
    loadPaperStats()
    loadPapers(1)
  } else if (val === 'institutions') {
    loadInstitutions()
  }
})

onMounted(() => {
  if (!authStore.isAdmin) {
    ElMessage.error('无权限访问')
    router.push('/')
    return
  }
  loadUsers()
  loadActiveUsersCount()
  loadOrders()
  loadUserQuotaList()
  loadRefundRequests()
})
</script>

<style scoped>
.admin-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.admin-header h2 {
  margin: 0;
  font-size: 30px;
  font-weight: 400;
  color: rgb(18, 18, 18);
}

.inst-hint {
  margin-left: 12px;
  font-size: 12px;
  color: rgb(107, 114, 128);
}

.admin-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  background: white;
  border-radius: 24px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(229, 231, 235, 0.50);
}

.stat-card.pending { border-top: 3px solid #e6a23c; }
.stat-card.approved { border-top: 3px solid rgb(0, 108, 73); }

.stat-num {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 36px;
  font-weight: 400;
  color: rgb(0, 108, 73);
}

.stat-label {
  font-size: 12px;
  color: rgb(113, 113, 122);
  margin-top: 4px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
}

.order-pagination {
  margin-top: 16px;
  justify-content: center;
  --el-color-primary: rgb(0, 108, 73);
  --el-color-primary-light-9: rgba(0, 108, 73, 0.1);
}

.admin-card {
  border-radius: 32px;
}

.admin-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.admin-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.stat-card.paid {
  border-top: 3px solid rgb(0, 108, 73);
}

:deep(.el-card) {
  border-radius: 32px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

:deep(.el-button--primary) {
  background: rgb(0, 108, 73);
  border-color: rgb(0, 108, 73);
  border-radius: 9999px;
}

:deep(.el-button--primary:hover) {
  background: rgb(0, 90, 60);
  border-color: rgb(0, 90, 60);
}
</style>
