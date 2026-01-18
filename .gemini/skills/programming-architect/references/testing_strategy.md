# 测试策略设计指南

## 核心使命

为软件项目设计全面、可执行的测试策略，确保代码质量和系统可靠性。

## 测试金字塔

```
          /\
         /  \
        / E2E \      ← 端到端测试（少量）
       /--------\
      /Integration\  ← 集成测试（适量）
     /--------------\
    /   Unit Tests   \ ← 单元测试（大量）
   /------------------\
```

### 各层测试比例建议
| 测试类型 | 比例 | 执行速度 | 维护成本 | 覆盖范围 |
|---------|------|---------|---------|---------|
| 单元测试 | 70% | 毫秒级 | 低 | 函数/类 |
| 集成测试 | 20% | 秒级 | 中 | 模块交互 |
| E2E测试 | 10% | 分钟级 | 高 | 完整流程 |

## 单元测试

### 设计原则：FIRST
- **F**ast：快速执行
- **I**ndependent：相互独立
- **R**epeatable：可重复
- **S**elf-validating：自验证
- **T**imely：及时编写

### 测试结构：AAA模式
```python
def test_user_registration():
    # Arrange - 准备测试数据
    user_data = {
        "name": "张三",
        "email": "zhangsan@example.com",
        "password": "SecurePass123"
    }
    
    # Act - 执行被测操作
    result = user_service.register(user_data)
    
    # Assert - 验证结果
    assert result.success == True
    assert result.user.name == "张三"
    assert result.user.id is not None
```

### 测试命名规范
```python
# 格式：test_[被测方法]_[场景]_[预期结果]

def test_calculate_discount_with_vip_user_returns_20_percent():
    pass

def test_validate_email_with_invalid_format_raises_validation_error():
    pass

def test_process_payment_when_balance_insufficient_returns_failure():
    pass
```

### 边界条件测试
```python
class TestUserAgeValidation:
    """年龄验证边界测试"""
    
    def test_age_at_minimum_boundary(self):
        """最小边界：18岁"""
        assert validate_age(18) == True
        
    def test_age_below_minimum(self):
        """低于最小边界：17岁"""
        assert validate_age(17) == False
        
    def test_age_at_maximum_boundary(self):
        """最大边界：120岁"""
        assert validate_age(120) == True
        
    def test_age_above_maximum(self):
        """高于最大边界：121岁"""
        assert validate_age(121) == False
        
    def test_age_zero(self):
        """零值"""
        assert validate_age(0) == False
        
    def test_age_negative(self):
        """负值"""
        assert validate_age(-1) == False
```

## 集成测试

### 测试范围
- 数据库交互
- 外部API调用
- 消息队列
- 缓存系统
- 文件系统

### 数据库集成测试
```python
import pytest
from app.repositories import UserRepository

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

class TestUserRepository:
    def test_create_and_find_user(self, db_session):
        # Arrange
        repo = UserRepository(db_session)
        user = User(name="测试用户", email="test@example.com")
        
        # Act
        created = repo.create(user)
        found = repo.find_by_id(created.id)
        
        # Assert
        assert found is not None
        assert found.name == "测试用户"
        assert found.email == "test@example.com"
```

### 外部服务Mock
```python
from unittest.mock import Mock, patch

class TestPaymentService:
    @patch('app.services.payment.StripeClient')
    def test_process_payment_success(self, mock_stripe):
        # Arrange
        mock_stripe.charge.return_value = {
            "id": "ch_123",
            "status": "succeeded"
        }
        service = PaymentService(mock_stripe)
        
        # Act
        result = service.process_payment(amount=100, card_token="tok_visa")
        
        # Assert
        assert result.success == True
        mock_stripe.charge.assert_called_once_with(
            amount=100,
            source="tok_visa"
        )
```

## 端到端测试

### 测试场景设计
```gherkin
Feature: 用户注册流程
  作为新用户
  我希望能够注册账号
  以便使用系统功能

  Scenario: 成功注册
    Given 我在注册页面
    When 我输入有效的用户名 "zhangsan"
    And 我输入有效的邮箱 "zhangsan@example.com"
    And 我输入符合要求的密码 "SecurePass123!"
    And 我点击注册按钮
    Then 我应该看到注册成功提示
    And 我应该收到验证邮件

  Scenario: 邮箱已被注册
    Given 邮箱 "existing@example.com" 已被注册
    And 我在注册页面
    When 我使用该邮箱尝试注册
    Then 我应该看到 "该邮箱已被注册" 的错误提示
```

### Playwright E2E测试
```python
from playwright.sync_api import Page, expect

def test_user_login_flow(page: Page):
    # 访问登录页
    page.goto("/login")
    
    # 输入凭据
    page.fill('[data-testid="email-input"]', "user@example.com")
    page.fill('[data-testid="password-input"]', "password123")
    
    # 点击登录
    page.click('[data-testid="login-button"]')
    
    # 验证登录成功
    expect(page).to_have_url("/dashboard")
    expect(page.locator('[data-testid="welcome-message"]')).to_contain_text("欢迎")
```

## TDD工作流

### 红-绿-重构循环

```mermaid
graph LR
    A[写失败测试<br>红色] --> B[写最少代码<br>使测试通过]
    B --> C[测试通过<br>绿色]
    C --> D[重构代码<br>保持绿色]
    D --> A
```

### TDD实践示例

```python
# Step 1: 写失败的测试（红）
def test_calculate_order_total():
    order = Order()
    order.add_item(Product("苹果", 10), quantity=2)
    order.add_item(Product("香蕉", 5), quantity=3)
    
    assert order.total == 35  # 失败：Order类还不存在

# Step 2: 写最少代码使测试通过（绿）
class Order:
    def __init__(self):
        self.items = []
    
    def add_item(self, product, quantity):
        self.items.append((product, quantity))
    
    @property
    def total(self):
        return sum(p.price * q for p, q in self.items)

# Step 3: 重构（保持绿）
class Order:
    def __init__(self):
        self._items: List[OrderItem] = []
    
    def add_item(self, product: Product, quantity: int) -> None:
        self._items.append(OrderItem(product, quantity))
    
    @property
    def total(self) -> Decimal:
        return sum(item.subtotal for item in self._items)
```

## 测试覆盖率

### 覆盖率类型
| 类型 | 说明 | 建议目标 |
|------|------|---------|
| 行覆盖 | 执行的代码行比例 | ≥ 80% |
| 分支覆盖 | 执行的条件分支比例 | ≥ 75% |
| 函数覆盖 | 调用的函数比例 | ≥ 90% |

### 配置示例（pytest）
```ini
# pytest.ini
[pytest]
addopts = --cov=app --cov-report=html --cov-fail-under=80
testpaths = tests
```

### 覆盖率报告
```bash
# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 输出
Name                      Stmts   Miss  Cover
---------------------------------------------
app/services/user.py        50      5    90%
app/services/order.py       80     12    85%
app/repositories/user.py    30      3    90%
---------------------------------------------
TOTAL                      160     20    87%
```

## 测试策略模板

### 项目测试计划
```markdown
# [项目名称] 测试策略

## 1. 测试范围

### 包含
- 用户模块：注册、登录、权限
- 订单模块：创建、支付、取消
- 商品模块：CRUD、搜索、库存

### 排除
- 第三方支付回调（使用Mock）
- 短信发送（使用Mock）

## 2. 测试类型分配

| 模块 | 单元测试 | 集成测试 | E2E测试 |
|------|---------|---------|---------|
| 用户模块 | 30个 | 10个 | 3个 |
| 订单模块 | 40个 | 15个 | 5个 |
| 商品模块 | 25个 | 8个 | 2个 |

## 3. 测试环境

| 环境 | 用途 | 数据 |
|------|------|------|
| Local | 单元测试 | Mock数据 |
| CI | 集成测试 | 测试数据库 |
| Staging | E2E测试 | 生产镜像 |

## 4. 质量门禁

- 代码覆盖率 ≥ 80%
- 所有测试通过
- 无严重安全漏洞
- 性能基准测试通过

## 5. 测试时间表

| 阶段 | 活动 | 时间 |
|------|------|------|
| 开发期 | 单元测试随代码提交 | 持续 |
| PR合并 | 集成测试自动运行 | CI |
| 发布前 | E2E测试全量执行 | 2小时 |
```

## 质量检查清单

### 单元测试检查
- [ ] 是否覆盖了核心业务逻辑？
- [ ] 是否测试了边界条件？
- [ ] 是否测试了异常场景？
- [ ] 测试是否独立、可重复？

### 集成测试检查
- [ ] 是否覆盖了关键接口？
- [ ] 是否正确Mock了外部依赖？
- [ ] 是否验证了数据一致性？

### E2E测试检查
- [ ] 是否覆盖了核心用户流程？
- [ ] 是否在类生产环境执行？
- [ ] 是否有失败重试机制？

## 初始化

作为测试策略专家，我可以帮助你：
- 设计项目测试金字塔
- 编写各类测试用例
- 配置CI/CD测试流程
- 分析和提升测试覆盖率

请告诉我你的项目测试需求。
