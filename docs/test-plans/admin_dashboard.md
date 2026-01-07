# Admin Dashboard - Test Plan

## Page Overview

**URL**: `/admin`  
**Page Type**: Dashboard (Read-only overview)  
**Auth Required**: Yes (redirects to `/Account/Login` if not authenticated)  
**Priority**: P1 (Core navigation hub, but read-only display)

### Purpose
Admin Dashboard serves as the landing page after authentication, displaying:
- User profile summary (email, username, authentication status)
- Verification status (email/phone)
- User roles
- System configuration (localization, enabled features count)

### Risk Assessment
| Risk Area | Impact | Likelihood | Priority |
|-----------|--------|------------|----------|
| Auth bypass (unauthenticated access) | High | Low | P0 |
| Incorrect user info display | Medium | Medium | P1 |
| Verification status mismatch with backend | Medium | Low | P1 |
| Role display inaccuracy | Medium | Low | P1 |
| Navigation access control bypass | High | Low | P0 |

### Priority Rationale
- **P0 Tests**: Authentication enforcement, navigation accessibility
- **P1 Tests**: Data display accuracy (user info, verification status, roles, system config)
- **Security Tests**: Minimal (read-only page; main concerns are auth/authorization)

## Element Mapping

All locators follow Playwright best practices (role > label > testid > aria > semantic CSS).

### Navigation
| Element | Selector | Description |
|---------|----------|-------------|
| Logo Link | `role=link[name='Aevatar AI']` | Main logo, redirects to `/` |
| Home Link | `role=link[name='Home']` | Dashboard link (current page) |
| Users Link | `role=link[name*='Users']` | Users management |
| Roles Link | `role=link[name*='Roles']` | Roles management |
| Workflow Link | `role=link[name='Workflow']` | Workflow page |
| Settings Link | `role=link[name*='Settings']` | Settings page |
| User Menu Toggle | `role=button[name='Toggle user menu']` | Profile menu |

### Dashboard Content
| Element | Selector | Description |
|---------|----------|-------------|
| Welcome Heading | `role=heading[name='Welcome back, User']` | Main heading |
| User Email | `text=admin-test01@test.com` | Displayed email (dynamic) |
| Username | `text=/Username:\s*admin-test01/` | Displayed username (dynamic) |
| Auth Badge | `text=Authenticated` | Authentication status |
| Email Verification | `text=Email Verification >> .. >> text=Not Verified` | Email verification status |
| Phone Verification | `text=Phone Verification >> .. >> text=Not Verified` | Phone verification status |
| User Roles | `text=Roles >> .. >> text=default` | User roles (dynamic) |
| Current Culture | `text=/Current Culture:\s*English/` | Localization setting |
| Default Resource | `text=/Default Resource:\s*BusinessServer/` | Resource name |
| Enabled Features | `text=/Enabled Features:\s*\d+/` | Feature count |

## Test Case Design

### P0 - Critical Path

#### TC-AdminDash-P0-001: Authentication Enforcement
**Objective**: Verify unauthenticated users are redirected to login  
**Precondition**: User is **not** authenticated  
**Steps**:
1. Navigate to `/admin` without authentication
2. Verify redirect to `/Account/Login`
3. Verify `returnUrl` parameter contains `/admin`

**Expected**:
- Status code: 302 (redirect) or immediate client-side navigation
- Final URL: `/Account/Login?returnUrl=%2Fadmin` (or similar)
- No dashboard content is visible

**Evidence**: Full-page screenshot, network logs

---

#### TC-AdminDash-P0-002: Authenticated User Dashboard Load
**Objective**: Verify authenticated user can access dashboard and see core elements  
**Precondition**: User is authenticated (account pool: `default` role)  
**Steps**:
1. Login with test account (via account pool)
2. Navigate to `/admin`
3. Verify page loads successfully (no redirect)
4. Verify presence of:
   - Welcome heading
   - User email
   - Username
   - Authenticated badge
   - User Profile card
   - System Configuration card

**Expected**:
- URL remains `/admin`
- All core elements are visible
- No error messages

**Evidence**: Full-page screenshot

---

### P1 - Functional Validation

#### TC-AdminDash-P1-001: User Info Display Accuracy
**Objective**: Verify displayed user info matches the authenticated session  
**Precondition**: User is authenticated (known account from pool)  
**Steps**:
1. Login with test account (record username/email)
2. Navigate to `/admin`
3. Extract displayed email
4. Extract displayed username
5. Extract displayed role(s)

**Expected**:
- Displayed email matches account pool email
- Displayed username matches account pool username
- Displayed role(s) match account permissions

**Evidence**: Screenshot with annotations, JSON comparison of expected vs actual

---

#### TC-AdminDash-P1-002: Verification Status Display
**Objective**: Verify verification status badges match backend state  
**Precondition**: User is authenticated  
**Steps**:
1. Navigate to `/admin`
2. Extract email verification status
3. Extract phone verification status
4. (Optional) Query backend `/api/identity/my-profile` for ground truth

**Expected**:
- Email verification status: "Not Verified" or "Verified" (matches backend)
- Phone verification status: "Not Verified" or "Verified" (matches backend)

**Evidence**: Screenshot, API response comparison

---

#### TC-AdminDash-P1-003: System Configuration Display
**Objective**: Verify system configuration card shows correct localization and feature count  
**Precondition**: User is authenticated  
**Steps**:
1. Navigate to `/admin`
2. Extract "Current Culture" value
3. Extract "Default Resource" value
4. Extract "Enabled Features" count

**Expected**:
- Current Culture: "English" (or matches backend `currentCulture.displayName`)
- Default Resource: "BusinessServer" (matches backend `defaultResourceName`)
- Enabled Features: Integer (matches backend feature count)

**Evidence**: Screenshot, comparison with `abp_app_config.json`

---

#### TC-AdminDash-P1-004: Navigation Links Accessibility
**Objective**: Verify all navigation links are functional and lead to correct pages  
**Precondition**: User is authenticated with `default` role  
**Steps**:
1. Navigate to `/admin`
2. Click each navigation link in sequence:
   - Home → verify remains on `/admin`
   - Users → verify navigates to users page (if permitted)
   - Roles → verify navigates to roles page (if permitted)
   - Workflow → verify navigates to `/workflow`
   - Settings → verify navigates to settings page (if permitted)

**Expected**:
- Each link navigates to expected URL
- If user lacks permission, appropriate message or redirect occurs (no crash)

**Evidence**: Screenshot per navigation, URL log

---

### Security - Minimal Set

#### TC-AdminDash-Sec-001: Direct URL Access Without Auth
**Objective**: Confirm unauthenticated direct URL access is blocked  
**Precondition**: No authentication (fresh incognito context)  
**Steps**:
1. Attempt direct navigation to `/admin`
2. Verify redirect to login

**Expected**:
- No dashboard content visible
- Redirect to `/Account/Login`

**Evidence**: Screenshot, network trace

---

#### TC-AdminDash-Sec-002: Role-Based Navigation Visibility
**Objective**: Verify navigation links respect role permissions  
**Precondition**: User authenticated with limited role (e.g., `default` with no admin rights)  
**Steps**:
1. Navigate to `/admin`
2. Check if "Users" and "Roles" links are visible/enabled
3. (If visible) Click and verify authorization enforcement on target page

**Expected**:
- If user lacks permission: link may be hidden, disabled, or target page shows access denied
- No unauthorized access to restricted resources

**Evidence**: Screenshot, error message capture

---

## Test Data Design

### Account Pool Requirement
- **Role**: `default` (basic authenticated user)
- **Status**: Active, authenticated
- **Verification**: Email/phone verification status should be **known** (either verified or not) for accurate assertion

### Test Data Files
- `test-data/admin_dashboard_data.json` (minimal; mostly read-only assertions)

```json
{
  "expected_defaults": {
    "current_culture_display": "English",
    "default_resource": "BusinessServer",
    "auth_badge_text": "Authenticated"
  },
  "verification_statuses": {
    "email_not_verified": "Not Verified",
    "email_verified": "Verified",
    "phone_not_verified": "Not Verified",
    "phone_verified": "Verified"
  },
  "navigation_links": [
    { "name": "Home", "expected_url_pattern": "/admin" },
    { "name": "Users", "expected_url_pattern": "/users", "requires_permission": true },
    { "name": "Roles", "expected_url_pattern": "/roles", "requires_permission": true },
    { "name": "Workflow", "expected_url_pattern": "/workflow" },
    { "name": "Settings", "expected_url_pattern": "/settings", "requires_permission": true }
  ]
}
```

---

## Backend Rules (Evidence-Based)

Extracted from `docs/test-plans/artifacts/admin_dashboard/abp_app_config.json`:

### Password Policy
- RequiredLength: **6**
- RequiredUniqueChars: **1**
- RequireNonAlphanumeric: **True**
- RequireLowercase: **True**
- RequireUppercase: **True**
- RequireDigit: **True**

*(Note: Password policy is not directly tested on dashboard, but documented for reference)*

### SignIn Policy
- RequireConfirmedEmail: **False**
- EnablePhoneNumberConfirmation: **True**
- RequireConfirmedPhoneNumber: **False**

### User Policy
- IsUserNameUpdateEnabled: **True**
- IsEmailUpdateEnabled: **True**

---

## Automation Recommendations

### Page Object
- **Location**: `pages/admin_dashboard_page.py`
- **Base**: Extend `core.base_page.BasePage`
- **Methods**:
  - `navigate()` → navigate to `/admin`
  - `get_user_email()` → extract displayed email
  - `get_username()` → extract displayed username
  - `get_user_roles()` → extract displayed role(s)
  - `get_email_verification_status()` → extract email verification badge text
  - `get_phone_verification_status()` → extract phone verification badge text
  - `get_current_culture()` → extract current culture display
  - `get_default_resource()` → extract default resource name
  - `get_enabled_features_count()` → extract enabled features count
  - `click_navigation_link(link_name)` → click a nav link by name

### Test File Structure
```
tests/
  admin/
    dashboard/
      __init__.py
      test_dashboard_p0_auth_enforcement.py
      test_dashboard_p0_authenticated_load.py
      test_dashboard_p1_user_info_accuracy.py
      test_dashboard_p1_verification_status.py
      test_dashboard_p1_system_config.py
      test_dashboard_p1_navigation.py
      test_dashboard_security.py
```

### Fixtures
- `auth_page` (from `core.fixture.auth`): Authenticated browser context
- `unauth_page` (from `core.fixture.auth`): Unauthenticated context for redirect tests
- `test_account` (from account pool): Test user credentials and metadata

### Markers
- `@pytest.mark.P0` for critical auth/load tests
- `@pytest.mark.P1` for functional validation
- `@pytest.mark.security` for security tests

### Allure Integration
- `@allure.feature("AdminDashboard")`
- `@allure.story("AuthEnforcement" / "UserInfo" / "Navigation" / "Security")`
- Attach screenshots and JSON diffs for all assertions

---

## Known Limitations & Assumptions

1. **Read-Only Page**: Dashboard is display-only; no user input validation required
2. **Dynamic Content**: User email/username/roles are dynamic based on authenticated account; tests must use account pool
3. **Permissions**: Navigation link visibility/functionality may vary by role; tests should cover both `default` and admin roles
4. **Localization**: Current plan assumes English locale; future tests may cover other languages
5. **Feature Flags**: "Enabled Features" count depends on backend feature configuration; tests should assert count is >= 0, not a fixed value

---

## Evidence Chain

All evidence stored in `docs/test-plans/artifacts/admin_dashboard/`:
- `page.png` - Full-page screenshot (authenticated state)
- `visible.txt` - Page text structure and hierarchy
- `abp_app_config.json` - ABP backend configuration snapshot (rules source of truth)
- `metadata.json` - Element locators and extracted rules summary

---

## Next Steps (Manual Execution Before Code Generation)

1. ✅ Review test plan for completeness
2. ⬜ Confirm account pool has suitable test accounts (default role, known verification status)
3. ⬜ Run manual exploratory test to validate element selectors
4. ⬜ Generate Page Object: `pages/admin_dashboard_page.py`
5. ⬜ Generate test data: `test-data/admin_dashboard_data.json`
6. ⬜ Generate test cases: `tests/admin/dashboard/*.py`
7. ⬜ Execute tests and generate Allure report

---

**Plan Author**: Generated via `@.cursor/rules/ui-test-plan-generator.mdc`  
**Generated Date**: 2025-12-30  
**Target Framework**: Playwright + Pytest + Allure

