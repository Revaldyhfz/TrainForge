# seeds demo data for the marker — idempotent, safe to re-run

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Appointment,
    AppointmentStatus,
    BodyMeasurement,
    Client,
    ClientStatus,
    Exercise,
    ExerciseType,
    Profile,
    ProgressLog,
    Subscription,
    SubscriptionPlanType,
    SubscriptionStatus,
    TrainingPlan,
    UserRole,
)


class Command(BaseCommand):
    help = 'Populate the database with demo data for review.'

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write('Demo data already present, skipping')
            return

        self.stdout.write('Creating users...')
        admin = User.objects.create_user(
            username='admin',
            email='admin@trainforge.demo',
            password='AdminPass123!',
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        Profile.objects.create(user=admin, role=UserRole.ADMIN)

        james = User.objects.create_user(
            username='james',
            email='james@trainforge.demo',
            password='TrainerPass123!',
            first_name='James',
            last_name='Doe',
        )
        Profile.objects.create(user=james, role=UserRole.TRAINER)

        amy = User.objects.create_user(
            username='amy',
            email='amy@trainforge.demo',
            password='TrainerPass123!',
            first_name='Amy',
            last_name='Lee',
        )
        Profile.objects.create(user=amy, role=UserRole.TRAINER)

        ryan = User.objects.create_user(
            username='ryan',
            email='ryan@trainforge.demo',
            password='TrainerPass123!',
            first_name='Ryan',
            last_name='Kim',
        )
        Profile.objects.create(user=ryan, role=UserRole.TRAINER)

        self.stdout.write('Creating subscriptions...')
        Subscription.objects.create(
            trainer=james,
            plan_type=SubscriptionPlanType.PRO,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=SubscriptionStatus.ACTIVE,
        )
        Subscription.objects.create(
            trainer=amy,
            plan_type=SubscriptionPlanType.BASIC,
            start_date=date(2026, 2, 15),
            end_date=date(2027, 2, 14),
            status=SubscriptionStatus.ACTIVE,
        )
        Subscription.objects.create(
            trainer=ryan,
            plan_type=SubscriptionPlanType.PRO,
            start_date=date(2025, 3, 1),
            end_date=date(2026, 2, 28),
            status=SubscriptionStatus.ARCHIVED,
        )

        self.stdout.write('Creating clients...')
        sarah = Client.objects.create(
            trainer=james,
            name='Sarah Chen',
            email='sarah.chen@example.com',
            phone='+61 412 345 001',
            goals='Weight loss, flexibility',
            status=ClientStatus.ACTIVE,
        )
        marcus = Client.objects.create(
            trainer=james,
            name='Marcus Liu',
            email='marcus.liu@example.com',
            phone='+61 412 345 002',
            goals='Muscle gain, strength',
            status=ClientStatus.ACTIVE,
        )
        emma = Client.objects.create(
            trainer=james,
            name='Emma Torres',
            email='emma.torres@example.com',
            phone='+61 412 345 003',
            goals='General fitness',
            status=ClientStatus.ACTIVE,
        )
        david = Client.objects.create(
            trainer=james,
            name='David Park',
            email='david.park@example.com',
            phone='+61 412 345 004',
            goals='Marathon training, endurance',
            status=ClientStatus.ACTIVE,
        )
        # client model has active/inactive only — using inactive in place of archived
        Client.objects.create(
            trainer=james,
            name='Jenna Kim',
            email='jenna.kim@example.com',
            phone='+61 412 345 005',
            goals='Posture, mobility',
            status=ClientStatus.INACTIVE,
        )

        tom = Client.objects.create(
            trainer=amy,
            name='Tom Reeves',
            email='tom.reeves@example.com',
            phone='+61 412 345 006',
            goals='Powerlifting prep',
            status=ClientStatus.ACTIVE,
        )
        Client.objects.create(
            trainer=amy,
            name='Lisa Wong',
            email='lisa.wong@example.com',
            phone='+61 412 345 007',
            goals='Postpartum recovery',
            status=ClientStatus.ACTIVE,
        )

        self.stdout.write('Creating training plans and exercises...')

        sarah_plan = TrainingPlan.objects.create(
            trainer=james, client=sarah, title='12-Week Strength Program',
        )
        sarah_squat = Exercise.objects.create(
            training_plan=sarah_plan,
            name='Barbell Squat',
            exercise_type=ExerciseType.REPS,
            sets=4, reps=8,
            description='Focus on depth and bracing',
            order_index=1,
        )
        Exercise.objects.create(
            training_plan=sarah_plan,
            name='Bench Press',
            exercise_type=ExerciseType.REPS,
            sets=4, reps=8,
            description='Pause on chest for 1 sec',
            order_index=2,
        )
        Exercise.objects.create(
            training_plan=sarah_plan,
            name='Deadlift',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=5,
            description='Conventional stance',
            order_index=3,
        )
        # plank spec was 60 sec; duration_minutes is an integer so storing 1 minute
        Exercise.objects.create(
            training_plan=sarah_plan,
            name='Plank',
            exercise_type=ExerciseType.DURATION,
            sets=3, duration_minutes=1,
            description='Keep core tight',
            order_index=4,
        )

        marcus_plan = TrainingPlan.objects.create(
            trainer=james, client=marcus, title='Hypertrophy Plan',
        )
        marcus_curl = Exercise.objects.create(
            training_plan=marcus_plan,
            name='Dumbbell Curl',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=12,
            order_index=1,
        )
        Exercise.objects.create(
            training_plan=marcus_plan,
            name='Lat Pulldown',
            exercise_type=ExerciseType.REPS,
            sets=4, reps=10,
            order_index=2,
        )
        Exercise.objects.create(
            training_plan=marcus_plan,
            name='Shoulder Press',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=10,
            order_index=3,
        )
        Exercise.objects.create(
            training_plan=marcus_plan,
            name='Tricep Pushdown',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=12,
            order_index=4,
        )

        david_plan = TrainingPlan.objects.create(
            trainer=james, client=david, title='Marathon Build',
        )
        david_long_run = Exercise.objects.create(
            training_plan=david_plan,
            name='Long Run',
            exercise_type=ExerciseType.DISTANCE,
            sets=1, distance_km=Decimal('10'),
            description='Easy pace, conversational',
            order_index=1,
        )
        Exercise.objects.create(
            training_plan=david_plan,
            name='Tempo Run',
            exercise_type=ExerciseType.DISTANCE,
            sets=1, distance_km=Decimal('5'),
            description='Comfortably hard',
            order_index=2,
        )
        Exercise.objects.create(
            training_plan=david_plan,
            name='Squat',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=10,
            description='Strength accessory',
            order_index=3,
        )

        emma_plan = TrainingPlan.objects.create(
            trainer=james, client=emma, title='Mobility Foundation',
        )
        Exercise.objects.create(
            training_plan=emma_plan,
            name='Cat-Cow Stretch',
            exercise_type=ExerciseType.REPS,
            sets=2, reps=10,
            order_index=1,
        )
        # pigeon spec was 45 sec; duration_minutes is an integer so storing 1 minute
        Exercise.objects.create(
            training_plan=emma_plan,
            name='Pigeon Pose',
            exercise_type=ExerciseType.DURATION,
            sets=2, duration_minutes=1,
            order_index=2,
        )

        tom_plan = TrainingPlan.objects.create(
            trainer=amy, client=tom, title='Powerlifting Prep',
        )
        Exercise.objects.create(
            training_plan=tom_plan,
            name='Back Squat',
            exercise_type=ExerciseType.REPS,
            sets=5, reps=5,
            order_index=1,
        )
        Exercise.objects.create(
            training_plan=tom_plan,
            name='Bench Press',
            exercise_type=ExerciseType.REPS,
            sets=5, reps=5,
            order_index=2,
        )
        Exercise.objects.create(
            training_plan=tom_plan,
            name='Deadlift',
            exercise_type=ExerciseType.REPS,
            sets=3, reps=3,
            order_index=3,
        )

        self.stdout.write('Creating appointments...')
        now = timezone.now()
        today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        today_3pm = now.replace(hour=15, minute=0, second=0, microsecond=0)

        Appointment.objects.create(
            trainer=james, client=sarah, title='Strength session',
            scheduled_at=today_9am - timedelta(weeks=2),
            duration_minutes=60,
            status=AppointmentStatus.COMPLETED,
        )
        Appointment.objects.create(
            trainer=james, client=sarah, title='Strength session',
            scheduled_at=today_9am - timedelta(weeks=1),
            duration_minutes=60,
            status=AppointmentStatus.COMPLETED,
        )
        Appointment.objects.create(
            trainer=james, client=sarah, title='Strength session',
            scheduled_at=today_9am,
            duration_minutes=60,
            status=AppointmentStatus.SCHEDULED,
        )
        Appointment.objects.create(
            trainer=james, client=sarah, title='Strength session',
            scheduled_at=today_9am + timedelta(days=7),
            duration_minutes=60,
            status=AppointmentStatus.SCHEDULED,
        )

        Appointment.objects.create(
            trainer=james, client=marcus, title='Hypertrophy session',
            scheduled_at=today_noon - timedelta(days=5),
            duration_minutes=60,
            status=AppointmentStatus.COMPLETED,
        )
        Appointment.objects.create(
            trainer=james, client=marcus, title='Hypertrophy session',
            scheduled_at=today_noon + timedelta(days=3),
            duration_minutes=60,
            status=AppointmentStatus.SCHEDULED,
        )

        Appointment.objects.create(
            trainer=james, client=emma, title='Mobility session',
            scheduled_at=today_3pm,
            duration_minutes=60,
            status=AppointmentStatus.SCHEDULED,
        )

        Appointment.objects.create(
            trainer=james, client=david, title='Long run check-in',
            scheduled_at=today_9am + timedelta(days=5),
            duration_minutes=60,
            status=AppointmentStatus.SCHEDULED,
        )

        self.stdout.write('Creating progress logs...')
        sarah_squat_weights = [
            Decimal('40'), Decimal('42.5'), Decimal('45'),
            Decimal('47.5'), Decimal('50'), Decimal('52.5'),
        ]
        for i, weight in enumerate(sarah_squat_weights):
            weeks_ago = 6 - i
            ProgressLog.objects.create(
                client=sarah, exercise=sarah_squat,
                logged_at=now - timedelta(weeks=weeks_ago),
                sets_completed=4, reps_completed=8, weight_kg=weight,
            )

        marcus_curl_weights = [Decimal('10'), Decimal('11'), Decimal('12.5'), Decimal('14')]
        for i, weight in enumerate(marcus_curl_weights):
            weeks_ago = 4 - i
            ProgressLog.objects.create(
                client=marcus, exercise=marcus_curl,
                logged_at=now - timedelta(weeks=weeks_ago),
                sets_completed=3, reps_completed=12, weight_kg=weight,
            )

        david_distances = [Decimal('8'), Decimal('10'), Decimal('12')]
        for i, dist in enumerate(david_distances):
            weeks_ago = 3 - i
            ProgressLog.objects.create(
                client=david, exercise=david_long_run,
                logged_at=now - timedelta(weeks=weeks_ago),
                sets_completed=1, distance_km=dist,
            )

        self.stdout.write('Creating body measurements...')
        today = timezone.localdate()
        sarah_weights = [
            Decimal('72.0'), Decimal('71.5'), Decimal('71.2'),
            Decimal('70.8'), Decimal('70.5'), Decimal('70.1'),
        ]
        for i, w in enumerate(sarah_weights):
            weeks_ago = 6 - i
            BodyMeasurement.objects.create(
                client=sarah, weight_kg=w,
                logged_at=today - timedelta(weeks=weeks_ago),
            )

        marcus_weights = [Decimal('75.0'), Decimal('75.5'), Decimal('76.2'), Decimal('76.8')]
        for i, w in enumerate(marcus_weights):
            weeks_ago = 4 - i
            BodyMeasurement.objects.create(
                client=marcus, weight_kg=w,
                logged_at=today - timedelta(weeks=weeks_ago),
            )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully'))
