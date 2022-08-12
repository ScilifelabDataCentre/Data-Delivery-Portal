"""Global application routes.

Most of the app routes are in `dds_web/web/user.py`.
Here we have the routes that are not specific to a user.
"""
from flask import Blueprint, render_template, jsonify
from flask import current_app as app
from dds_web import forms

pages = Blueprint("pages", __name__)


@pages.route("/", methods=["GET"])
def home():
    """Home page."""
    form = forms.LoginForm()
    return render_template("home.html", form=form)


@pages.route("/policy", methods=["GET"])
def open_policy():
    """Show privacy policy."""
    return render_template("policy.html")

@pages.route("/trouble", methods=["GET"])
def open_troubleshooting():
    """Show troubleshooting document."""
    import requests
    response = requests.get("https://scilifelab.atlassian.net/wiki/rest/api/content/2192998470?expand=space,metadata.labels,body.storage")
    response_json = response.json()
    info = response_json["body"]["storage"]["value"]
    info = info.replace("<h2>", "<br><h2>")
    # info = info.replace("</h2>", "</h2><br>")
    return render_template("troubleshooting.html", info=info)

@pages.route("/status")
def get_status():
    """Return a simple status message to confirm that the system is ready."""
    return jsonify({"status": "ready"})


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template("404.html"), 404
