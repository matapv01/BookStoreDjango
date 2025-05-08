BOOKSTORE PROJECT FEATURES AND TESTING

1. User Management
-----------------
Features:
- User registration with email/password
- User roles: regular users, staff, and superadmins
- User status tracking (active/inactive)
- Password management and reset
- Staff privileges management

Admin Features:
- Reset user passwords
- Change user roles
- Activate/deactivate users
- Grant/revoke staff privileges

Testing:
- UserAdminTest covers admin actions and permissions
- Tests verify proper role changes and access control
- Password reset functionality testing
- Staff privilege management testing

2. Book Management
-----------------
Features:
- Book categorization
- Stock tracking
- Sales tracking
- Price management
- Book details and descriptions

Admin Features:
- Manage book inventory
- Update book details
- Track book sales
- Manage categories

3. Shopping Cart
---------------
Features:
- Add/remove books
- Update quantities
- Cart persistence
- Stock validation
- Price calculations

Testing:
- Stock level checks
- Price calculation verification
- Cart persistence tests
- Multiple item handling

4. Order Processing
------------------
Features:
- Order creation from cart
- Order status tracking
- Payment status tracking
- Order history

Testing:
- Order creation tests
- Status updates
- Payment processing
- Order item verification

5. Permission System
-------------------
Access Levels:
- Regular users: browse and purchase
- Staff: manage books and basic user operations
- Superadmin: full system access

Testing:
- Permission checks for each level
- Access control verification
- Role-based action tests

6. API Endpoints
---------------
Main Routes:
- /register/: User registration
- /login/: User authentication
- /books/: Book listings
- /cart/: Shopping cart management
- /checkout/: Order processing
- /admin/: Administration interface

Admin Routes:
- /store/admin/user/reset-password/: Password reset
- /store/admin/user/change-role/: Role management
- Admin interface URLs for model management

7. Testing Coverage
------------------
Unit Tests:
- Models: Data integrity and relationships
- Views: Request handling and responses
- Forms: Data validation and processing
- Admin: Custom actions and permissions

Test Categories:
- Authentication tests
- Permission tests
- Data manipulation tests
- Integration tests
- Admin functionality tests

Test Execution:
python manage.py test store.tests

8. Security Features
-------------------
- Password hashing
- Permission-based access control
- Form validation
- CSRF protection
- Session management
- Staff privilege controls

9. Database Models
-----------------
Core Models:
- Users: Custom user model
- Category: Book categories
- Books: Book information
- Order: Purchase orders
- Cart: Shopping cart
- CartBooks: Cart items

10. Development Notes
--------------------
Test Database:
- Uses SQLite for testing
- Automatic migration handling
- Test data cleanup

Admin Interface:
- Custom admin actions
- Role-based access control
- Bulk operations support
- Custom form handling

11. API Response Format
----------------------
Success Responses:
1. List operations (GET):
   {
     "items": [...],
     "total": "0.00"  // If applicable
   }

2. Detail operations (GET):
   {
     "id": 1,
     "title": "...",
     "price": "0.00",
     ...
   }

3. Action responses (POST):
   {
     "status": "success",
     "message": "Action completed",
     "redirect": "url"  // If applicable
   }

Error Responses:
{
    "error": "Error message"
}

HTTP Status Codes:
- 200: Successful GET/valid form submission
- 302: Successful redirect after action
- 400: Bad request/validation error
- 403: Permission denied
- 404: Resource not found
- 405: Method not allowed

12. Test Case Details
--------------------
User Admin Tests:
1. test_user_list_display:
   - Verifies admin list view access
   - Checks permission requirements
   - Expected: 200 OK for staff

2. test_reset_password:
   - Tests password reset action
   - Verifies password change
   - Expected: 302 redirect success

3. test_make_inactive:
   - Tests user deactivation
   - Verifies status change
   - Expected: 302 redirect success

4. test_make_staff:
   - Tests staff promotion
   - Verifies role changes
   - Expected: 302 redirect success

5. test_user_change_form:
   - Tests user edit form
   - Verifies field updates
   - GET Expected: 200 OK
   - POST Expected: 302 redirect

13. Common Use Cases and Data Flows
---------------------------------
User Registration Flow:
1. User submits registration form
2. System validates email uniqueness
3. Password is hashed
4. User account created
5. Redirect to login

Shopping Flow:
1. User browses book catalog
2. Adds books to cart
3. System validates stock
4. Cart total updated
5. Checkout process
6. Order creation
7. Stock update
8. Payment processing

14. Development Environment
-------------------------
Requirements:
- Python 3.8+
- Django 3.2+
- SQLite (development)
- pytest for testing

Setup:
1. Clone repository
2. Create virtual environment
3. Install requirements
4. Run migrations
5. Create superuser
6. Load test data

15. Project Structure
-------------------
bookstore_project/
├── store/
│   ├── models.py      # Database models
│   ├── views.py       # View logic
│   ├── admin.py       # Admin interface
│   ├── forms.py       # Form definitions
│   ├── urls.py        # URL routing
│   └── tests.py       # Test cases
├── templates/         # HTML templates
└── static/           # Static files

16. Quick Start Guide
-------------------
1. Clone Repository:
   git clone [repository-url]
   cd bookstore_project

2. Setup Environment:
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install Dependencies:
   pip install -r requirements.txt

4. Database Setup:
   python manage.py migrate
   python manage.py createsuperuser

5. Run Tests:
   python manage.py test store.tests

6. Start Development Server:
   python manage.py runserver

7. Access Admin Interface:
   http://localhost:8000/admin/
