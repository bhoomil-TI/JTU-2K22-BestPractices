from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError
from django.contrib.auth.models import User
import logging
from restapi.models import Category, Groups, UserExpense, Expenses


class UserSerializer(ModelSerializer):
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta(object):
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }


class CategorySerializer(ModelSerializer):
    class Meta(object):
        model = Category
        fields = '__all__'


class GroupSerializer(ModelSerializer):
    members = UserSerializer(many=True, required=False)

    class Meta(object):
        model = Groups
        fields = '__all__'


class UserExpenseSerializer(ModelSerializer):
    class Meta(object):
        model = UserExpense
        fields = ['user', 'amount_owed', 'amount_lent']


class ExpensesSerializer(ModelSerializer):
    users = UserExpenseSerializer(many=True, required=True)

    def create(self, validated_data):
        expense_users = validated_data.pop('users')
        expense = Expenses.objects.create(**validated_data)
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        return expense

    def update(self, instance, validated_data):
        user_expenses = validated_data.pop('users')
        instance.description = validated_data['description']
        instance.category = validated_data['category']
        instance.group = validated_data.get('group', None)
        instance.total_amount = validated_data['total_amount']

        if user_expenses:
            instance.users.all().delete()
            UserExpense.objects.bulk_create(
                [
                    user_expense(expense=instance, **user_expense)
                    for user_expense in user_expenses
                ],
            )
        instance.save()
        return instance

    def validate(self, attrs):
        # user = self.context['request'].user
        try:
            user_ids = [user['user'].id for user in attrs['users']]
            if len(set(user_ids)) != len(user_ids):
                raise ValidationError('Single user appears multiple times')
        except ValidationError as e:
            logging.error(e)
        finally:
            return attrs

        # if data.get('group', None) is not None:
        #     group = Groups.objects.get(pk=data['group'].id)
        #     group_users = group.members.all()
        #     if user not in group_users:
        #         raise UnauthorizedUserException()
        #     for user in data['users']:
        #         if user['user'] not in group_users:
        #             raise ValidationError('Only group members should be listed in a group transaction')
        # else:
        #     if user.id not in user_ids:
        #         raise ValidationError('For non-group expenses, user should be part of expense')

        # total_amount = data['total_amount']
        # amount_owed = 0
        # amount_lent = 0
        # for user in data['users']:
        #     if user['amount_owed'] < 0 or user['amount_lent'] < 0 or total_amount < 0:
        #         raise ValidationError('Expense amounts must be positive')
        #     amount_owed += user['amount_owed']
        #     amount_lent += user['amount_lent']
        # if amount_lent != amount_owed or amount_lent != total_amount:
        #     raise ValidationError('Given amounts are inconsistent')


    class Meta(object):
        model = Expenses
        fields = '__all__'
