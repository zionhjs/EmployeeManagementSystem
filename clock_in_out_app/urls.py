from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login', views.login),
    path('login_verify', views.login_verify),
    path('logout', views.logout),
    path('register', views.register),
    path('register_verify', views.register_verify),
    path('clockinout', views.clockinout),
    path('clockinout/get_employee', views.get_employee),
    # path('clockinout/get_employee/admin', views.get_employee_admin),
    path('points/get_employee', views.get_employee_points),
    # path('dailyupdates/get_employee', views.get_employee_dailyupdates),
    path('clockin', views.clockin),
    path('clockout', views.clockout),
    path('clockout_lasttime', views.clockout_lasttime),

    path('points', views.points),
    path('report', views.report),
    #path('report/get_clock_add_report', views.get_clock_add_report),
    path('report/report_verify', views.report_verify),
    path('settings', views.settings),
    path('settings/reset_password', views.reset_password_verify),

    path('admin', views.admin),
    path('admin/edit_quote/<int:id>', views.edit_quote),
    path('admin/update_quote/<int:id>', views.update_quote),
    path('admin/award_extra_verify/<int:uid>/<int:cid>', views.award_extra_verify),
    path('dailyupdates/award_extra_verify/<int:uid>/<int:rid>',
         views.report_award_extra_verify),
    path('admin/edit_employee_verify/<int:uid>', views.edit_employee_verify),

    path('dailyupdates', views.dailyupdates),
    path('dailyupdates/updates_get_employee_id', views.updates_get_employee_id),
]
