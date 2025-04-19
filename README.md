# FIN - Budgeting & Expense Estimation Planner

FIN is an AI-powered financial assistant that helps users manage their budgets, track expenses, and get personalized financial advice.

## Features

- Create and manage monthly budgets
- Plan and optimize travel budgets
- Track expenses and savings
- Set financial goals
- Get personalized financial advice
- Access up-to-date bank FD rates
- Compare banking products

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

5. Run the application:
```bash
streamlit run streamlit_app.py
```

## Deployment

### Option 1: Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your environment variables (GOOGLE_API_KEY)
5. Deploy!

### Option 2: Heroku

1. Create a `Procfile`:
```
web: streamlit run streamlit_app.py
```

2. Deploy to Heroku:
```bash
heroku create
git push heroku main
```

3. Set environment variables:
```bash
heroku config:set GOOGLE_API_KEY=your_api_key_here
```

## Environment Variables

- `GOOGLE_API_KEY`: Your Google API key for Gemini AI

## Made by
Ankit Kumar (12312618)
   