# Testing Guide for Resources and Achievements Pages

## 🔐 Authentication Required

The Resources and Achievements pages require authentication to work properly. Here's how to test them:

### Step 1: Sign In to the Frontend

1. **Start the frontend**: `cd frontend && npm run dev`
2. **Go to**: `http://localhost:3000` (or whatever port it shows)
3. **You'll be redirected to sign in page**
4. **Use these test credentials**:
   - **Email**: `demo.user@procert.test`
   - **Password**: `TestUser123!`

### Step 2: Test the Pages

Once signed in, you should see the navigation menu with all pages including:
- Dashboard
- AI Chat  
- Practice Quizzes
- Progress
- Study Path
- **Resources** ← Click this
- **Achievements** ← Click this

### Step 3: Expected Behavior

#### Resources Page (`/resources`)
- ✅ Should show a grid of 13 AWS certifications
- ✅ Should have search and filter functionality
- ✅ Clicking on a certification should show actual S3 bucket contents
- ✅ Should display real files like "AWS Certified Cloud Practitioner Sample Questions.pdf"

#### Achievements Page (`/achievements`)
- ✅ Should show achievement statistics at the top
- ✅ Should display achievement cards with progress bars
- ✅ Should show earned vs unearned achievements
- ✅ Should have category filtering (Study Time, Quiz Mastery, etc.)

## 🐛 Troubleshooting

### If you see CORS errors:
- Make sure you're signed in with the test credentials above
- The API requires authentication - unauthenticated requests will fail

### If pages don't show navigation:
- Make sure you're accessing through the main app, not directly via URL
- Start from `http://localhost:3000` and sign in first

### If no data loads:
- Check browser console for authentication errors
- Make sure the test user exists (run `python3 create_test_user_for_frontend.py` if needed)

## ✅ Backend API Status

The backend API is working correctly:
- ✅ `/resources/{certification}` endpoint is live
- ✅ S3 integration is working
- ✅ Authentication is properly configured
- ✅ CORS is configured for authenticated requests

## 🧪 Direct API Testing

You can test the API directly with:
```bash
python3 test_resources_with_auth.py
```

This should show successful responses with actual S3 bucket contents.