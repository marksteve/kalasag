import requests
from flask import (abort, Blueprint, current_app, flash, redirect,
                   render_template, request, session, url_for)

from . import db

blueprint = Blueprint("example", __name__, static_folder='static')


@blueprint.route("/", methods=["GET", "POST"])
def index():
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  else:
    return redirect(url_for("views.index"))

  user_id = session.get("example_user_id")

  if app and user_id:
    user = db.hgetall("apps:{}:users:{}".format(
      app["client_id"],
      user_id,
    ))
  else:
    user = None

  return render_template(
    "example/index.html",
    app=app,
    user=user,
  )

@blueprint.route("/tryOTP", methods=["GET", "POST"])
def tryOTP():
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  else:
    return redirect(url_for("views.index"))

  user_id = session.get("example_user_id")

  if app and user_id:
    user = db.hgetall("apps:{}:users:{}".format(
      app["client_id"],
      user_id,
    ))
  else:
    user = None

  return render_template(
    "example/try_otp.html",
    app=app,
    user=user,
  )


@blueprint.route("/add_user", methods=["POST"])
def add_user():
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  else:
    return redirect(url_for("views.index"))

  if request.method == "POST":
    res = requests.put(
      url_for(
        "api_user",
        client_id=app["client_id"],
        user_id=request.form["user_id"],
        _external=True,
      ),
      data=dict(
        secret_key=app["secret_key"],
        name=request.form["user_name"],
        number=request.form["user_number"],
      ),
    )
    if res.status_code != requests.codes.ok:
      abort(500)
    session["example_user_id"] = request.form["user_id"]
  return redirect(url_for("example.tryOTP"))


@blueprint.route("/login", methods=["GET","POST"])
def login():
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  else:
    return redirect(url_for("views.index"))

  if "example_user_id" not in session:
    return redirect(url_for(".index"))

  res = requests.post(
    url_for(
      "api_otp_request",
      client_id=app["client_id"],
      user_id=session["example_user_id"],
      _external=True,
    ),
    data=dict(
      secret_key=app["secret_key"],
    ),
  )
  if res.status_code != requests.codes.ok:
    abort(500)
  return redirect(url_for(".validate"))


@blueprint.route("/validate", methods=["GET", "POST"])
def validate():
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  else:
    return redirect(url_for("views.index"))

  if "example_user_id" not in session:
    return redirect(url_for(".index"))

  if request.method == "POST":
    current_app.logger.debug("SENDING: " + request.form["code"])
    res = requests.post(
      url_for(
        "api_otp_validate",
        client_id=app["client_id"],
        user_id=session["example_user_id"],
        _external=True,
      ),
      data=dict(
        code=request.form["code"],
        secret_key=app["secret_key"],
      ),
    )
    if res.status_code != requests.codes.ok:
      abort(500)
    if res.json()["valid"]:
      session.pop('example_user_id')
      return render_template("example/success.html")
    else:
      current_app.logger.debug(res.json())
      flash("Login failed")
  return render_template("example/validate.html", app=app)

