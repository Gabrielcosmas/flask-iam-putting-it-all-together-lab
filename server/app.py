#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio')
        image_url = data.get('image_url')

        if not username or not password:
            return {'error': '422: Unprocessable Entity'}, 422

        try:
            user = User(
                username=username,
                bio=bio,
                image_url=image_url
            )
            user.password_hash = password

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            return user.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return user.to_dict(), 200
        return {'error': '401: Unauthorized'}, 401


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter(User.username == username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200

        return {'error': '401: Unauthorized'}, 401


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return {}, 204
        return {'error': '401: Unauthorized'}, 401


class Recipes(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401: Unauthorized'}, 401

        recipes = [
            recipe.to_dict() 
            for recipe in Recipe.query.filter(Recipe.user_id == user_id).all()
        ]
        return recipes, 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401: Unauthorized'}, 401

        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422


class RecipeByID(Resource):
    def get(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401: Unauthorized'}, 401

        recipe = Recipe.query.filter(Recipe.id == id).first()
        if not recipe:
            return {'error': '404: Not Found'}, 404
        return recipe.to_dict(), 200

    def patch(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401: Unauthorized'}, 401

        recipe = Recipe.query.filter(Recipe.id == id).first()
        if not recipe:
            return {'error': '404: Not Found'}, 404

        data = request.get_json()
        for attr in data:
            setattr(recipe, attr, data[attr])

        try:
            db.session.commit()
            return recipe.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

    def delete(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401: Unauthorized'}, 401

        recipe = Recipe.query.filter(Recipe.id == id).first()
        if not recipe:
            return {'error': '404: Not Found'}, 404

        db.session.delete(recipe)
        db.session.commit()
        return {}, 204


# API Routes
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(Recipes, '/recipes', endpoint='recipes')
api.add_resource(RecipeByID, '/recipes/<int:id>', endpoint='recipe_by_id')

if __name__ == '__main__':
    app.run(port=5555, debug=True)