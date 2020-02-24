from django.db import models
import re

# Create your models here.


class UserManager(models.Manager):
    def basic_validator(self, postData):
        errors = {}
        EMAIL_REGEX = re.compile(
            r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = ("Invalid email address!")
        if len(postData['first_name']) < 2:
            errors['first_name'] = " First Name should be at least 2 characters and letters only!"
        if len(postData['last_name']) < 2:
            errors['last_name'] = "Last Name should be at least 2 characters and letters only!"
        if len(postData['password']) < 8:
            errors['password'] = "Password should be at least 8 characters!"
        return errors

    def basic_validator_password(self, postData):
        errors = {}
        if len(postData['password']) < 8:
            errors['password'] = "Password should be at least 8 characters!"
        return errors

    def basic_validator_edit(self, postData):
        errors = {}
        EMAIL_REGEX = re.compile(
            r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = ("Invalid email address!")
        if len(postData['first_name']) < 2:
            errors['first_name'] = " First Name should be at least 2 characters and letters only!"
        if len(postData['last_name']) < 2:
            errors['last_name'] = "Last Name should be at least 2 characters and letters only!"
        return errors


class User(models.Model):
    email = models.CharField(max_length=125)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    password = models.CharField(max_length=255)
    points_rate = models.IntegerField(default=1)
    total_points = models.IntegerField(default=0)
    description = models.CharField(
        max_length=255, default="default description")
    user_level = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()


class Clock(models.Model):
    clockin = models.DateTimeField(null=True, blank=True)
    clockout = models.DateTimeField(null=True, blank=True)
    clock_hours = models.FloatField(default=0.00)
    clock_points = models.FloatField(default=0.00)
    task_des = models.CharField(max_length=255, default="")
    user = models.ForeignKey(User, related_name="clocks",
                             on_delete=models.CASCADE)  # one to many
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DailyReport(models.Model):
    recipients = models.CharField(max_length=255)
    done = models.CharField(max_length=255)
    challenges = models.CharField(max_length=255)
    helps = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name="user_reports",
                             on_delete=models.CASCADE, default=None)  # one to many
    clock = models.ForeignKey(Clock, related_name="clock_reports",
                              on_delete=models.CASCADE, default=None)  # one to many
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Award(models.Model):
    points = models.FloatField(default=0.00)
    admin = models.ForeignKey(
        User, related_name="admin_awards", on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(
        User, related_name="user_awards", on_delete=models.CASCADE, default=None)
    clock = models.ForeignKey(
        Clock, related_name="clock_awards", on_delete=models.CASCADE, default=None)
    reasons = models.CharField(
        max_length=255, default="some good default reason")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Quote(models.Model):
    quote = models.CharField(max_length=255)
    author = models.CharField(max_length=55)
    onEdit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
