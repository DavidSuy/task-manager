from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order, update_task_priority, list_tasks
from services.users import get_user
from utils.errors import AppError, ValidationError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    priority_raw = request.args.get("priority")
    priority = None
    if priority_raw is not None:
        try:
            priority = int(priority_raw)
        except ValueError:
            raise ValidationError("priority", "must be an integer")
    return jsonify(list_tasks(priority))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    title = data.get("title")
    user_id = data["user_id"]
    kwargs = {"priority": data["priority"]} if "priority" in data else {}
    return jsonify(create_task(title, user_id, **kwargs)), 201

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_priority_route(task_id):
    data = request.get_json()
    priority = data.get("priority")
    return jsonify(update_task_priority(task_id, priority)), 200

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))
