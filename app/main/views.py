#coding:utf8

from flask import render_template, session, redirect, url_for, flash, current_app, abort, request, make_response
from flask.ext.login import login_required, current_user
from ..decorators import admin_required, permission_required
from . import main
from .forms import PostForm, CommentForm,EditProfileForm, EditProfileAdminForm
from .. import db
from ..models import User,Role,Post,Comment,Permission
from ..email import send_email


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    #posts = user.posts.order_by(Post.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False
    )
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, endpoint='main.user', pagination=pagination)



@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form =CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author=current_user._get_current_object(),
                          post=post)
        db.session.add(comment)
        db.session.commit()
        flash(u'评论成功!')
        return redirect(url_for('main.post',id=post.id, page=-1))
    page = request.args.get('page',1, type=int)
    if page == -1:
        page = (post.comments.count() -1 ) / current_app.config['FLASK_POSTS_PER_PAGE'] +1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False
    )

    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False
    )
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    print comment.disabled
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate', page=request.args.get('ppage', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    print comment.disabled
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash(u'文档已更新!')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)



@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u'提交成功!')
        return redirect(url_for('main.user',username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)


@main.route('/index', methods=['GET', 'POST'])
#@login_required
def index():

    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('main.index'))
    #posts = Post.query.order_by(Post.timestamp.desc()).all()


    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
        print show_followed
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, endpoint='main.index', pagination=pagination, show_followed=show_followed)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash(u'你已经关注这个用户了.')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash(u'你关注了: {0}'.format(username))
    return redirect(url_for('main.user', username=username))





@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash(u'你没有关注{0}'.format(username))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    flash(u'你取消了对 {0} 关注'.format(username))
    return redirect(url_for('main.user', username=username))



@main.route('/followers/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect('main.index')
    page = request.args.get('page', 1 , type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    follows = [ {'user': item.follower, 'timestamp': item.timestamp } for item in pagination.items if item.follower.username != username ]
    return render_template('followers.html', user=user, title=u'关注你的人', endpoint='main.followers', pagination=pagination, follows=follows)


@main.route('/following/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def following(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('main.user'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    follows = [ {'user': item.followed, 'timestamp': item.timestamp } for item in pagination.items if item.followed.username != username ]
    return render_template('followers.html', user=user, title=u'你关注的人', endpoint='main.following', pagination=pagination, follows=follows)


# @main.route('/index',methods=['POST','GET'])
# @login_required
# def index():
#     form = NameForm()
#     form.name.data = 'kefatong@qq.com'
    # if form.validate_on_submit():
    #     user = User.query.filter_by(username=form.name.data).first()
    #
    #     if not user:
    #         print user
    #         if current_app.config['FLASK_ADMIN']:
    #             send_email(current_app.config['FLASK_ADMIN'],'New User','email/user', user=form.name.data)
    #         user = User(username=form.name.data)
    #         db.session.add(user)
    #         session['known'] = False
    #         flash('pleased to meet you.')
    #     else:
    #         session['known'] = True
    #         flash('happy to see you again!')
    #
    #     session['name'] = form.name.data
    #     return redirect(url_for('main.index'))
    # return render_template('index.html', name=session.get('name'), form=form, known=session.get('known', False))


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash(u'修改资料成功!')
        return redirect(url_for('main.user',username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html',form=form,user=user)
#print url_for('index')

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For Administrators!'


@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
    return 'For moderators!'

if __name__ == '__main__':
    manager.run()
    #app.run(host='0.0.0.0',debug=True)
