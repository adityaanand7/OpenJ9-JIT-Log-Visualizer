import os
from flask import Flask
from routes import log_viewer_bp

# Small app factory so setup stays in one place.
def create_app():
    app = Flask(__name__)

    # Keep runtime folders ready so first upload/view works without manual setup.
    base_dir = os.path.dirname(__file__)
    os.makedirs(os.path.join(base_dir, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'uploads'), exist_ok=True)

    # Serve the viewer from root routes.
    app.register_blueprint(log_viewer_bp, url_prefix="/")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
