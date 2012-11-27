#-*- coding:utf-8 -*-
#个人过往页
import datetime
from collections import defaultdict
from flask import (g, render_template, request, 
        redirect, abort, flash, url_for)
from past import app
from past import config
from past import consts

from past.model.user import User
from past.model.status import Status, get_status_ids_today_in_history
from .utils import require_login, check_access_user, statuses_timelize, get_sync_list

@app.route("/i")
@app.route("/")
def home():
    if not g.user:
        return render_template("anonymous_home.html", **locals())

    return redirect("/past")

@app.route("/<uid>/past")
def user_past(uid):
    user = User.get(uid)
    if not user:
        abort(404, "no such user")
    try:
        now = datetime.datetime.strptime(request.args.get("now"), "%Y-%m-%d")
    except:
        now = datetime.datetime.now()

    #history_ids = get_status_ids_today_in_history(g.user.id, now) 
    history_ids = Status.get_ids(8, start=0, limit=50)
    status_list = Status.gets(history_ids)
    status_list  = statuses_timelize(status_list)
    sync_list = get_sync_list(g.user)

    d = defaultdict(list)
    for x in status_list:
        t = x.create_time.strftime("%Y年%m月%d日")
        d[t].append(x)
    history_status = d

    print "-------history:", history_status

    return render_template("v2/user_past.html", **locals())

@app.route("/past")
@require_login()
def my_past():
    user = g.user
    return redirect(url_for(".user_past", uid=user.id))

@app.route("/user/<uid>")
def user(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")
    return redirect("/%s" % uid)

@app.route("/<uid>")
def user_by_domain(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = check_access_user(u)
    if r:
        flash(r[1].decode("utf8"), "tip")
        return redirect(url_for("home"))

    ids = Status.get_ids(user_id=u.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    if g.user and g.user.id == uid:
        pass
    elif g.user and g.user.id != uid:
        status_list = [x for x in status_list if x.privacy() != consts.STATUS_PRIVACY_PRIVATE]
    elif not g.user:
        status_list = [x for x in status_list if x.privacy() == consts.STATUS_PRIVACY_PUBLIC]
        
    status_list  = statuses_timelize(status_list)
    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    if g.user:
        sync_list = get_sync_list(g.user)
    else:
        sync_list = []

    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    return render_template("v2/user.html", user=u, intros=intros, 
            status_list=status_list, config=config, sync_list=sync_list, 
            now = now)
