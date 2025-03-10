from ...security_wraps import admin_only, manager_only, not_logged_in_only, Confirmed_RSI_only
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, set_access_cookies, current_user, create_refresh_token, set_refresh_cookies, get_jwt
from .. import api_v0 as api

from flask import jsonify, request

from corp_system.controllers.security_manager import SecurityManager

@api.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout current user
    
    This allow a user to logout from the api
    ---
    
    operationId: logout
    tags:
        - Security
    security:
        - corp_access_pass: []
    responses:
      200:
        description: Transfer was successful
      401:
        $ref: "#/components/responses/unauthorized"

    """
   
    try:
        response = SecurityManager.logout_user()
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400
    
    return response