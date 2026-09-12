from flask import Flask, jsonify, request
import os
import boto3
import psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

S3_BUCKET = os.environ["S3_BUCKET"]

s3 = boto3.client("s3")


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "resource not found"
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "internal server error"
    }), 500


@app.route("/health", methods=["GET"])
def health():
    connection = None

    try:
        connection = get_db_connection()
        connection.close()
        connection = None

        return jsonify({
            "status": "healthy",
            "service": "flask-api",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception:
        app.logger.exception("Health check failed")

        if connection:
            connection.close()

        return jsonify({
            "status": "unhealthy",
            "service": "flask-api",
            "database": "disconnected"
        }), 500


@app.route("/api/users", methods=["GET"])
def get_users():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users ORDER BY id;"
        )

        rows = cursor.fetchall()

        users = [
            {
                "id": row[0],
                "name": row[1],
                "email": row[2]
            }
            for row in rows
        ]

        return jsonify(users), 200

    except Exception:
        app.logger.exception("Failed to fetch users")

        return jsonify({
            "error": "failed to fetch users"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({
            "error": "name and email are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email;
            """,
            (data["name"], data["email"])
        )

        row = cursor.fetchone()

        connection.commit()

        return jsonify({
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }), 201

    except psycopg2.errors.UniqueViolation:
        if connection:
            connection.rollback()

        return jsonify({
            "error": "email already exists"
        }), 409

    except Exception:
        if connection:
            connection.rollback()

        app.logger.exception("Failed to create user")

        return jsonify({
            "error": "failed to create user"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@app.route("/api/files", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({
            "error": "file is required"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "filename is required"
        }), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({
            "error": "invalid filename"
        }), 400

    try:
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            filename
        )

        return jsonify({
            "message": "file uploaded successfully",
            "bucket": S3_BUCKET,
            "key": filename
        }), 201

    except Exception:
        app.logger.exception("Failed to upload S3 file")

        return jsonify({
            "error": "file upload failed"
        }), 500


@app.route("/api/files", methods=["GET"])
def list_files():
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET
        )

        objects = response.get("Contents", [])

        files = [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            }
            for obj in objects
        ]

        return jsonify({
            "files": files
        }), 200

    except Exception:
        app.logger.exception("Failed to list S3 files")

        return jsonify({
            "error": "failed to list files"
        }), 500


@app.route("/api/files/<path:filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key=filename
        )

        return jsonify({
            "message": "file deleted successfully",
            "key": filename
        }), 200

    except Exception:
        app.logger.exception("Failed to delete S3 file")

        return jsonify({
            "error": "failed to delete file"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
