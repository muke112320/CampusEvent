"""子路径部署支持测试（CAMPUSEVENT_URL_PREFIX=/campusevent）。"""

from __future__ import annotations

import pytest
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from tests.helpers import query_one


def _prefix_login(client, username: str = "s1"):
    client.post("/campusevent/logout")
    response = client.post(
        "/campusevent/login", data={"username": username}, follow_redirects=True
    )
    assert response.status_code == 200
    return response


@pytest.fixture
def prefixed_client(app):
    app.wsgi_app = DispatcherMiddleware(
        Response("Not Found", status=404, mimetype="text/plain"),
        {"/campusevent": app.wsgi_app},
    )
    return app.test_client()


def test_login_page_works_under_prefix(prefixed_client):
    response = prefixed_client.get("/campusevent/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/campusevent/static/style.css" in html
    assert 'action="/campusevent/login"' in html


def test_login_and_navigation_keep_prefix(prefixed_client):
    response = prefixed_client.post(
        "/campusevent/login",
        data={"username": "s1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert response.request.path == "/campusevent/activities"
    html = response.get_data(as_text=True)
    assert 'href="/campusevent/activities"' in html
    # session cookie 使用独立名称，避免与同主机其他应用冲突
    assert prefixed_client.get_cookie("campusevent_session") is not None


def test_cancel_redirect_keeps_prefix(prefixed_client, app, make_activity):
    activity = make_activity(title="子路径取消活动", capacity=2)
    _prefix_login(prefixed_client, "s1")
    prefixed_client.post(
        f"/campusevent/activities/{activity.activity_id}/register", follow_redirects=True
    )
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    response = prefixed_client.post(
        f"/campusevent/registrations/{registration['registration_id']}/cancel",
        data={"next": f"/activities/{activity.activity_id}"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/campusevent/activities/{activity.activity_id}"
