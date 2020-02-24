from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
import bcrypt
from datetime import datetime, timedelta
from decimal import Decimal
from random import choice
from queue import Queue

# Views
from django.http import JsonResponse


def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'login.html')


def logout(request):
    request.session.clear()
    return redirect('/')


def register(request):
    return render(request, 'register.html')


def login_verify(request):
    found_user = User.objects.filter(email=request.POST['email'])
    if len(found_user) < 1:
        messages.error(request, 'Invalid Credentials')
        return redirect('/login')
    else:
        logged_user = found_user[0]
        if bcrypt.checkpw(request.POST['password'].encode(), logged_user.password.encode()):
            request.session['this_user_id'] = logged_user.id
            return redirect('/clockinout')
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect('/login')


def register_verify(request):
    errors = User.objects.basic_validator(request.POST)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/')
    elif request.POST['password_confirm'] != request.POST['password']:
        messages.error(request, 'The password entered twice must be the same!')
    else:
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.POST['password']
        user_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        this_user = User.objects.create(email=email, first_name=first_name,
                            last_name=last_name, password=user_pwd)
        request.session['this_user_id'] = this_user.id
        first_user = User.objects.first()
        first_user.user_level = 9
        first_user.save()
        messages.success(request, "Register successfully!")
        return redirect('/clockinout')


def daily_quote():
    all_quotes = Quote.objects.all()
    quote_list = []
    for quote in all_quotes:
        quote_list.append(quote)
    last_quote = quote_list[-1]
    cur_date = datetime.now()
    if last_quote.updated_at.date() == cur_date.date():
        today_quote = last_quote
    elif last_quote.updated_at.date() < cur_date.date():
        today_quote = quote_list.pop(0)
        today_quote.updated_at = cur_date
        today_quote.save()
        quote_list.append(today_quote)
    return today_quote


def clockinout(request):  # unfinished
    this_id = request.session.get('this_user_id')
    if this_id:  # check login
        this_user = User.objects.get(id=this_id)
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        print("login_user total poinst:", total_points)
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        for user in User.objects.all():
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()

        clocks = Clock.objects.all().order_by('-created_at')
        
        if Clock.objects.last():
            last_clock = Clock.objects.last()
            last_clockout_choice = last_clock.clockin.replace(
                tzinfo=None)  # remove the timezone

            last_clockout_choice = last_clock.clockin

            lastclock_midnight_time = last_clockout_choice.replace(
                hour=23, minute=59, second=59, microsecond=0)

            last_clockout_choices = []

            while last_clockout_choice < lastclock_midnight_time:
                last_clockout_choices.append(last_clockout_choice)
                last_clockout_choice += timedelta(minutes=30)
        else:
            last_clock = {}
            last_clockout_choices = []
        
        if request.session.get('show_employee_id'):
            show_employee_id = request.session['show_employee_id']
            show_employee = User.objects.get(id=show_employee_id)
        else:
            show_employee = {}

        context = {
            "this_user": this_user,
            "show_employee": show_employee,
            "employees":User.objects.all(),
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices
        }
        return render(request, 'clockinout.html', context)
    else:
        messages.error(
                request, 'Needs to be logged in to visit the system!')
        return redirect('/')


def get_employee(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if request.POST['show_employee_id']:
            employee_id = request.POST['show_employee_id']
            this_employee = User.objects.get(id=employee_id)
            request.session['show_employee_id'] = employee_id
            messages.success(request, f"Successfully showing {this_employee.first_name}'s Clock Records!")
            return redirect('/clockinout')
        else:
            messages.error(request, "please select one employee and view his/her clocks!")
            return redirect('/clockinout')
    else:
        return redirect('/')


def clockout_lasttime(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    last_clock = Clock.objects.all().last()
    if this_id:  # check login
        if not last_clock.clockout:
            if request.POST['task_des']:
                last_clock.clockout = datetime.strptime(
                    request.POST['clock_out'], "%Y-%m-%d %H:%M")
                last_clock.task_des = request.POST['task_des']
                last_clock.save()
                return redirect('/clockinout')
            else:
                messages.error(
                    request, 'Must Provide Task Description')
                return redirect('/')
        else:
            messages.error(
                request, 'The last clockout is finished or the last clockin is in the same-day, please use clockout button for today or just clockin!')
            return redirect('/clockinout')
    else:
        return redirect('/')


def clockin(request):  # works
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:  # check login
        new_clock = Clock.objects.create(
            user=this_user, clockin=datetime.now())
        return redirect('/clockinout')
    else:
        return redirect('/')


def clockout(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:  # check login
        last_clock = Clock.objects.all().last()
        cur_date = datetime.now()
        if last_clock.clockin.date() == cur_date.date():
            task_des = request.POST['task_des']
            if not task_des:
                messages.error(request, 'Must Provide Task Description')
                return redirect('/clockinout')
            if not last_clock.clockin:
                return redirect('/clockinout')
            else:
                this_id = request.session.get('this_user_id')
                this_user = User.objects.get(id=this_id)
                last_clock.clockout = datetime.now()
                last_clock.task_des = task_des
                last_clock.save()
                return redirect('/clockinout')
        else:
            messages.error(
                request, 'the clockout time is not today, please check "forgot to clock out yesterday"')
            return redirect('/clockinout')
    else:
        return redirect('/')


def points(request):
    this_id = request.session.get('this_user_id')
    if this_id:
        this_user = User.objects.get(id=this_id)
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        all_users = User.objects.all()
        for user in all_users:
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()
        clocks = Clock.objects.all().order_by('-created_at')
        last_clock = Clock.objects.last()

        if request.session.get("show_employee_id"):
            clocks = clocks.filter(user = User.objects.get(id = request.session.get("show_employee_id")))

        last_clockout_choice = last_clock.clockin.replace(
            tzinfo=None)  # remove the timezone

        last_clockout_choice = last_clock.clockin

        lastclock_midnight_time = last_clockout_choice.replace(
            hour=23, minute=59, second=59, microsecond=0)

        last_clockout_choices = []

        while last_clockout_choice < lastclock_midnight_time:
            last_clockout_choices.append(last_clockout_choice)
            last_clockout_choice += timedelta(minutes=30)

        employees = User.objects.all()

        context = {
            "this_user": this_user,
            "employees":employees,
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices
        }
        return render(request, 'points.html', context)
    else:
        messages.error(
                request, 'Needs to be logged in to visit the system!')
        return redirect('/')


def report(request):
    this_id = request.session.get('this_user_id')
    if this_id:
        this_user = User.objects.get(id=this_id)
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        all_users = User.objects.all()
        for user in all_users:
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()
        clocks = Clock.objects.all().order_by('-created_at')
        last_clock = Clock.objects.last()

        last_clockout_choice = last_clock.clockin.replace(
            tzinfo=None)  # remove the timezone

        last_clockout_choice = last_clock.clockin

        lastclock_midnight_time = last_clockout_choice.replace(
            hour=23, minute=59, second=59, microsecond=0)

        last_clockout_choices = []

        while last_clockout_choice < lastclock_midnight_time:
            last_clockout_choices.append(last_clockout_choice)
            last_clockout_choice += timedelta(minutes=30)

        context = {
            "this_user": this_user,
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices
        }
        return render(request, 'report.html', context)
    else:
        messages.error(
                request, 'Needs to be logged in to visit the system!')
        return redirect('/')

# def get_clock_add_report(request):
#     this_id = request.session.get('this_user_id')
#     this_user = User.objects.get(id=this_id)
#     if this_id:
#         if request.POST['get_clock']:
#             request.session['report_clock_id'] = request.POST['get_clock']
#             return redirect('/report')
#         else:
#             messages.error(
#                     request, 'Needs to select a clock to do the report!')
#             return redirect('report')
#     else:
#         return redirect('/')


def report_verify(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if request.POST['get_clock']:
            request.session['report_clock_id'] = int(request.POST['get_clock'])
        else:
            messages.error(
                    request, 'Needs to select a clock to do the report!')
            return redirect('/report')

        cur_date = datetime.now()

        if this_user.user_reports:
            this_user_all_reports = this_user.user_reports.all()
            for report in this_user_all_reports:
                if report.created_at.date() == cur_date.date():
                    messages.error(
                    request, 'Same User Can\'t report twice in a single-day!')
                    return redirect('/report')

        recipients = request.POST['recipients']
        done = request.POST['done']
        challenges = request.POST['challenges']
        helps = request.POST['helps']
        if request.session.get('report_clock_id'):
            this_clock = Clock.objects.get(id = request.session.get('report_clock_id'))
            print("this_clock is:", this_clock)   #worked here 
            new_daily_report = DailyReport.objects.create(recipients=recipients, done=done, challenges=challenges, helps=helps, user=this_user, clock=this_clock)
            print("new_daily_report:", new_daily_report)    #worked here 
            request.session['report_clock_id'] = None
            messages.success(request, "Daily Report Successfully!")
            return redirect('/report')
        else:
            messages.error(
                request, 'Needs to select a clock to do the report!')
            return redirect('/report')
    else:
        return redirect('/')


def settings(request):
    this_id = request.session.get('this_user_id')
    if this_id:
        this_user = User.objects.get(id=this_id)
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        all_users = User.objects.all()
        for user in all_users:
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()
        clocks = Clock.objects.all().order_by('-created_at')
        last_clock = Clock.objects.last()

        last_clockout_choice = last_clock.clockin.replace(
            tzinfo=None)  # remove the timezone

        last_clockout_choice = last_clock.clockin

        lastclock_midnight_time = last_clockout_choice.replace(
            hour=23, minute=59, second=59, microsecond=0)

        last_clockout_choices = []

        while last_clockout_choice < lastclock_midnight_time:
            last_clockout_choices.append(last_clockout_choice)
            last_clockout_choice += timedelta(minutes=30)

        context = {
            "this_user": this_user,
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            # "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices
        }
        return render(request, 'settings.html', context)
    else:
        messages.error(
                request, 'Needs to be logged in to visit the system!')
        return redirect('/')


def reset_password_verify(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if bcrypt.checkpw(request.POST['previous_password'].encode(), this_user.password.encode()):
            errors = User.objects.basic_validator_password(request.POST)
            if len(errors) > 0:
                for key, value in errors.items():
                    messages.error(request, value)
                return redirect('/settings')
            elif request.POST['password_confirm'] != request.POST['password']:
                messages.error(
                    request, 'The password entered twice must be the same!')
                return redirect('/settings')
            else:
                new_password = request.POST['password']
                user_pwd = bcrypt.hashpw(
                    new_password.encode(), bcrypt.gensalt()).decode()
                this_user.password = user_pwd
                this_user.save()
                messages.success(request, "Reset Password Successfully!")
                return redirect('/settings')
        else:
            messages.error(
                request, 'Please Type in the Correct Previous-Password!')
            return redirect('/settings')
    else:
        return redirect('/')


def admin(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id and this_user.user_level == 9:  # check login
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        print("login_user total poinst:", total_points)
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        all_users = User.objects.all()
        for user in all_users:
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()

        clocks = Clock.objects.all().order_by('-created_at')
        
        if Clock.objects.last():
            last_clock = Clock.objects.last()
            last_clockout_choice = last_clock.clockin.replace(
                tzinfo=None)  # remove the timezone

            last_clockout_choice = last_clock.clockin

            lastclock_midnight_time = last_clockout_choice.replace(
                hour=23, minute=59, second=59, microsecond=0)

            last_clockout_choices = []

            while last_clockout_choice < lastclock_midnight_time:
                last_clockout_choices.append(last_clockout_choice)
                last_clockout_choice += timedelta(minutes=30)
        else:
            last_clock = {}
            last_clockout_choices = []
         
        context = {
            "this_user": this_user,
            "employees": User.objects.all(),
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices,
            "level_range": [0,1,2,3,4,5,6,7,8,9]
        }
        return render(request, 'admin.html', context)
    elif this_user.user_level < 9:
        return redirect('/clockinout')
    else:
        return redirect('/')


def edit_quote(request, id):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id and this_user.user_level == 9:
        this_quote = Quote.objects.get(id=id)
        this_quote.onEdit = True
        this_quote.save()
        return redirect('/admin')
    elif this_user.user_level < 9:
        return redirect('/clockinout')
    else:
        return redirect('/')


def update_quote(request, id):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id and this_user.user_level == 9:
        this_quote = Quote.objects.get(id=id)
        this_quote.quote = request.POST['quote']
        this_quote.author = request.POST['author']
        this_quote.onEdit = False
        this_quote.save()
        return redirect('/admin')
    elif this_user.user_level < 9:
        return redirect('/clockinout')
    else:
        return redirect('/')


def award_extra_verify(request, uid, cid):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        award_user = User.objects.get(id=uid)
        award_points = float(request.POST['point_value'])
        award_clock = Clock.objects.get(id=cid)
        award_clock.clock_points += award_points
        award_clock.save()
        reasons = request.POST['reasons']
        print(award_points)
        new_award = Award.objects.create(
            admin=this_user, user=award_user, clock=award_clock, points=award_points, reasons=reasons)
        return redirect('/admin')
    else:
        return redirect('/')

def report_award_extra_verify(request, uid, rid):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        award_user = User.objects.get(id=uid)
        award_points = float(request.POST['point_value'])
        award_report = DailyReport.objects.get(id=rid)
        award_clock = award_report.clock
        award_clock.clock_points += award_points
        award_clock.save()
        reasons = request.POST['reasons']
        print(award_points)
        new_award = Award.objects.create(
            admin=this_user, user=award_user, clock=award_clock, points=award_points, reasons=reasons)
        messages.success(request, f"Award {award_user.first_name} Extra {new_award.points} points successfully!")
        return redirect('/dailyupdates')
    else:
        return redirect('/')


def edit_employee_verify(request, uid):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        errors = User.objects.basic_validator_edit(request.POST)
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('/admin')
        else:
            edit_user = User.objects.get(id = uid)
            edit_user.first_name = request.POST['first_name']
            edit_user.last_name = request.POST['last_name']
            edit_user.email = request.POST['email']
            edit_user.points_rate = float(request.POST['points_rate'])
            edit_user.total_points = float(request.POST['total_points'])
            edit_user.save()
            messages.success(request, "Edit Employee Successfully!")
            return redirect('/admin')
    else:
        return redirect('/')

def dailyupdates(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id and this_user.user_level == 9:  # check login
        user_clocks = this_user.clocks.all()
        clock_hours = 0
        clock_points = 0
        total_points = 0
        for clock in user_clocks:
            if clock.clockin is not None and clock.clockout is not None:  # judgement statement
                time1 = clock.clockin
                time2 = clock.clockout
                time_delta = time2-time1
                total_secondes = int(time_delta.total_seconds())
                clock_hours = round(total_secondes/3600, 3)
                clock.clock_hours = clock_hours
                clock_points = round(clock_hours*this_user.points_rate, 3)
                if clock.clock_awards:
                    for award in clock.clock_awards.all():
                        clock_points += award.points
                clock.clock_points = clock_points
                clock.save()
                total_points += clock_points
            else:
                clock_points = 0
        this_user.total_points = total_points
        this_user.save()

        all_users_points = float(0.01)
        all_users = User.objects.all()
        for user in all_users:
            all_users_points += round(user.total_points, 2)

        today_quote = daily_quote()

        clocks = Clock.objects.all().order_by('-created_at')
        last_clock = Clock.objects.last()
        last_clockout_choice = last_clock.clockin.replace(
            tzinfo=None)  # remove the timezone

        last_clockout_choice = last_clock.clockin

        lastclock_midnight_time = last_clockout_choice.replace(
            hour=23, minute=59, second=59, microsecond=0)

        last_clockout_choices = []

        while last_clockout_choice < lastclock_midnight_time:
            last_clockout_choices.append(last_clockout_choice)
            last_clockout_choice += timedelta(minutes=30)
        
        get_report = {}
        if request.session.get('get_report_id'):
            get_report_id = request.session.get('get_report_id')
            get_report = DailyReport.objects.get(id = get_report_id)
            request.session['get_report_id'] = None
        else:
            get_report_id = None
        
        if get_report:
            pass
        else:
            get_report = {}

        print('get_report_id is:', get_report_id)
        print('session[get_report_id]:', request.session.get('get_report_id'))

        get_employee = {}
        if request.session.get('get_employee_id'):
            get_employee_id = request.session.get('get_employee_id')
            get_employee = User.objects.get(id = get_employee_id)
            request.session['get_employee_id'] = None
        else:
            get_employee_id = None
        
        if get_employee:
            pass
        else:
            get_employee = {}

        print('get_employee_id is:', get_employee_id)
        print('session[get_employee_id]:', request.session.get('get_employee_id'))

        context = {
            "this_user": this_user,
            "employees": User.objects.all(),
            "get_report_id":get_report_id,
            "get_report":get_report,
            "get_employee":get_employee,
            "today_quote": today_quote,
            "this_user_points": round(this_user.total_points, 2),
            "all_users_points": all_users_points,
            "clocks": clocks,
            "last_clock": last_clock,
            "date_cur": datetime.now().strftime("%H:%M %p. | %d-%M-%Y "),
            "last_clockout_choices": last_clockout_choices,
            "level_range": [0,1,2,3,4,5,6,7,8,9]
        }
        return render(request, 'dailyupdates.html', context)
    else:
        return redirect('/')

# def get_employee_admin(request):
#     this_id = request.session.get('this_user_id')
#     this_user = User.objects.get(id=this_id)
#     if this_id:
#         employee_id = request.POST['show_employee_id']
#         this_employee = User.objects.get(id=employee_id)
#         request.session['show_employee_id'] = employee_id
#         return redirect('/dailyupdates')
#     else:
#         return redirect('/')

def get_employee_points(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if request.POST['show_employee_id']:
            employee_id = request.POST['show_employee_id']
            this_employee = User.objects.get(id=employee_id)
            request.session['show_employee_id'] = employee_id
            messages.success(request, f"Successfully showing {this_employee.first_name}'s Clock Records!")
            return redirect('/points')
        else:
            messages.error(request, "please select one employee and view his/her clocks!")
            return redirect('/points')
    else:
        return redirect('/')

def updates_get_employee_id(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if request.POST.get('updates_get_employee_id'):
            updates_get_employee_id = request.POST['updates_get_employee_id']
            request.session['get_employee_id'] = updates_get_employee_id
            print("get_employee_id:", request.session.get('updates_get_employee_id'))
            return redirect('/dailyupdates')
        else:
            messages.error(request, 'Please Select an employee and only show his daily-updates!')
            return redirect('/dailyupdates')
    else:
        return redirect('/')

def get_report_id(request):
    this_id = request.session.get('this_user_id')
    this_user = User.objects.get(id=this_id)
    if this_id:
        if request.POST.get('get_report_id'):
            get_report_id = request.POST['get_report_id']
            request.session['get_report_id'] = get_report_id
            print("get_report_id:", request.session.get('get_report_id'))
            return redirect('/dailyupdates')
        else:
            messages.error(request, 'Please Select a Date to show this employee\'s report!')
            return redirect('/dailyupdates')
    else:
        return redirect('/')

