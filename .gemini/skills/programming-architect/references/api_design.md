# API设计与规范指南

## 核心使命

提供工业级的API设计方法论，确保设计出一致、可扩展、易用、安全的API接口。

## 设计原则

### 核心原则

1. **一致性**：整个API遵循统一的命名和行为规范
2. **直观性**：开发者可以凭直觉理解API用法
3. **渐进披露**：简单用例简单实现，复杂需求可扩展
4. **向后兼容**：版本迭代不破坏现有客户端

### RESTful设计规范

#### 资源命名
```
# 正确示例
GET    /users              # 获取用户列表
GET    /users/{id}         # 获取单个用户
POST   /users              # 创建用户
PUT    /users/{id}         # 更新用户
DELETE /users/{id}         # 删除用户

# 嵌套资源
GET    /users/{id}/orders           # 用户的订单列表
GET    /users/{id}/orders/{orderId} # 用户的特定订单

# 错误示例（避免）
GET    /getUsers           # ❌ 动词命名
GET    /user               # ❌ 单数形式
POST   /users/create       # ❌ URL中包含动词
```

#### HTTP方法语义
| 方法 | 语义 | 幂等性 | 安全性 | 典型用途 |
|------|------|--------|--------|---------|
| GET | 读取 | ✅ 是 | ✅ 是 | 获取资源，支持缓存 |
| POST | 创建 | ❌ 否 | ❌ 否 | 创建新资源，处理复杂操作 |
| PUT | 完整更新 | ✅ 是 | ❌ 否 | 替换整个资源 |
| PATCH | 部分更新 | ❌ 否 | ❌ 否 | 更新资源的部分字段 |
| DELETE | 删除 | ✅ 是 | ❌ 否 | 删除资源 |

#### 状态码规范
```
# 2xx 成功
200 OK           # 请求成功
201 Created      # 资源创建成功，返回Location头
204 No Content   # 成功但无返回内容（DELETE）

# 4xx 客户端错误
400 Bad Request       # 请求格式错误
401 Unauthorized      # 未认证
403 Forbidden         # 无权限
404 Not Found         # 资源不存在
409 Conflict          # 资源冲突
422 Unprocessable     # 请求格式正确但语义错误

# 5xx 服务端错误
500 Internal Error    # 服务器内部错误
502 Bad Gateway       # 网关错误
503 Service Unavailable # 服务不可用
```

## 请求与响应设计

### 请求格式

#### 查询参数
```
# 分页
GET /users?page=1&limit=20

# 排序
GET /users?sort=created_at&order=desc

# 过滤
GET /users?status=active&role=admin

# 字段选择
GET /users?fields=id,name,email

# 搜索
GET /users?q=john
```

#### 请求体结构
```json
{
  "data": {
    "type": "user",
    "attributes": {
      "name": "张三",
      "email": "zhangsan@example.com"
    },
    "relationships": {
      "department": {
        "id": "dept-123"
      }
    }
  }
}
```

### 响应格式

#### 成功响应
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "user-123",
    "name": "张三",
    "email": "zhangsan@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "meta": {
    "request_id": "req-abc123"
  }
}
```

#### 列表响应（带分页）
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {"id": "1", "name": "用户1"},
    {"id": "2", "name": "用户2"}
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

#### 错误响应
```json
{
  "code": 40001,
  "message": "参数验证失败",
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "邮箱格式不正确"
    },
    {
      "field": "password",
      "code": "TOO_SHORT",
      "message": "密码长度不能少于8位"
    }
  ],
  "meta": {
    "request_id": "req-abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 版本控制

### 版本策略

#### URL路径版本（推荐）
```
GET /api/v1/users
GET /api/v2/users
```

#### Header版本
```
GET /api/users
Accept: application/vnd.myapi.v1+json
```

### 版本迁移
```markdown
## 版本迁移指南

### 从 v1 迁移到 v2

#### 破坏性变更
1. `GET /users` 响应格式变更
   - v1: `{ "users": [...] }`
   - v2: `{ "data": [...], "pagination": {...} }`

2. 字段重命名
   - `created_time` → `created_at`
   - `modify_time` → `updated_at`

#### 迁移步骤
1. 更新客户端SDK
2. 修改响应解析逻辑
3. 切换API endpoint
```

## 认证与安全

### 认证方式

#### JWT Bearer Token
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### API Key
```http
X-API-Key: sk-xxxxxxxxxxxx
```

### 安全最佳实践

1. **传输安全**：强制使用HTTPS
2. **速率限制**：实施API调用限制
3. **输入验证**：严格验证所有输入
4. **敏感数据**：不在URL中传递敏感信息
5. **CORS配置**：正确配置跨域策略

### 速率限制响应
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1609459200
Retry-After: 60

{
  "code": 42901,
  "message": "请求过于频繁，请稍后重试",
  "retry_after": 60
}
```

## API文档规范

### OpenAPI规范示例
```yaml
openapi: 3.0.0
info:
  title: 用户管理API
  version: 1.0.0
  description: 用户管理相关接口

paths:
  /users:
    get:
      summary: 获取用户列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
```

## GraphQL设计（可选）

### Schema设计
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  orders(first: Int, after: String): OrderConnection!
}

type Query {
  user(id: ID!): User
  users(filter: UserFilter, first: Int, after: String): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}
```

## 质量检查清单

### 设计阶段
- [ ] 资源命名是否使用复数名词？
- [ ] HTTP方法是否语义正确？
- [ ] 是否有统一的响应格式？
- [ ] 是否设计了分页和过滤？
- [ ] 是否考虑了版本控制？

### 安全检查
- [ ] 是否强制HTTPS？
- [ ] 是否有认证机制？
- [ ] 是否有速率限制？
- [ ] 是否验证所有输入？
- [ ] 敏感数据是否保护？

### 文档检查
- [ ] 是否有完整的API文档？
- [ ] 是否包含请求/响应示例？
- [ ] 是否说明了错误码？
- [ ] 是否有版本迁移指南？

## 初始化

作为API设计专家，我可以帮助你：
- 设计RESTful或GraphQL API
- 制定API规范和文档标准
- 审查现有API设计
- 规划API版本迁移

请告诉我你的API设计需求。
