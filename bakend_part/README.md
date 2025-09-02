# Eye2 - Backend Diagnostic Platform

This is the backend for the Eye2 medical diagnostic platform, built with Django and Django Rest Framework.

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Magood1/eye2-ai-platform
    cd eye2_project
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Setup environment variables:**
    ```bash
    cp .env .env.example
    ```

5.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```


## Running Tests

To run the test suite:
```bash
pytest



## Frontend Development

The frontend is rendered using Django Template Language (DTL) and styled with Tailwind CSS via a CDN for rapid development.

### Running the Frontend

1.  Ensure you have run migrations and created a superuser or a doctor user.
2.  Run the development server:
    ```bash
    python manage.py runserver
    ```
3.  Log in at `http://127.0.0.1:8000/accounts/login/` with your user credentials.
4.  Navigate to the dashboard at `http://127.0.0.1:8000/`.

### Key Pages
-   **Dashboard:** `/`
-   **Patient List:** `/users/patients/`
-   **Login:** `/accounts/login/`

## Download AI Models

Due to the large file sizes of the model files (approximately 2 GB), these files have not been included in the repo to avoid exceeding GitHub's limits.

You can download the AI ​​models from the following link:
[Models Download Link](https://example.com/downloads/ai_models.zip)

After downloading, please extract the files and place them in the `ai_models` folder in the project.

Make sure the files are in the correct directory before running the server.

If you encounter any problems downloading the files, please contact us.