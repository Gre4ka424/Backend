# MeetHere - Social Platform for Events and Networking

## Project Structure

```
/
├── backend/               # Backend (FastAPI, PostgreSQL, Cloudinary)
│   ├── main.py            # Main FastAPI application
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database connection
│   └── ...
├── frontend/              # Frontend (HTML/CSS/JS)
│   ├── index.html         # Main page
│   ├── styles.css         # CSS styles
│   └── ...
├── Dockerfile             # For deployment on Railway
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Technologies
- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Cloudinary
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Docker, Railway

## Features
- User registration, authentication (JWT)
- User profile with photo (stored in Cloudinary)
- Event creation, editing, joining/leaving
- Event images (stored in Cloudinary)
- Admin panel for user/content management
- Responsive frontend

## Local Development

### Prerequisites
- Python 3.8+
- pip
- PostgreSQL (or use Railway cloud DB)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone [your-repo-url]
   cd [project-directory]
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the `backend/` directory with the following:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/dbname
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

4. **Run the backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

5. **Open the frontend:**
   - Open `frontend/index.html` in your browser
   - Or run a static server:
     ```bash
     cd frontend
     python -m http.server
     # Visit http://localhost:8000
     ```

## Deployment on Railway

1. **Push your code to GitHub.**
2. **Create a new Railway project and link your GitHub repo.**
3. **Add a PostgreSQL plugin in Railway.**
4. **Set environment variables in Railway:**
   - `DATABASE_URL` (Railway provides automatically)
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
5. **Deploy!** Railway will build and run your backend automatically.

## Database Migration
Tables are created automatically on first run using SQLAlchemy:
```python
Base.metadata.create_all(bind=engine)
```
No manual migration is needed for initial setup.

## Cloudinary Integration
- All user profile photos and event images are uploaded to Cloudinary.
- Only the public URL is stored in the database.
- No images are stored locally in production.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret

## Contacts
For questions or suggestions, please contact [your email]. 
