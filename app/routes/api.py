from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from app import db
from app.models.ai_log import AILog
from app.services.ai_service import process_ai_chat, match_products_by_intent

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat_endpoint():
    data = request.get_json() or {}
    message_text = data.get('message', '').strip()

    if not message_text:
        return jsonify({'success': False, 'message': 'Message text is required.'}), 400

    # Retrieve session conversation context
    ai_context = session.get('ai_context', [])

    # Process via AI Service
    result = process_ai_chat(message_text, context_history=ai_context)

    # Append to session context (keep last 5 interactions)
    ai_context.append({
        'user_query': message_text,
        'matched_categories': result.get('matched_categories', []),
        'product_ids': result.get('product_ids', [])
    })
    session['ai_context'] = ai_context[-5:]

    # Log query to MySQL DB for Admin AI Analytics
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        cat_matched = ", ".join(result.get('matched_categories', [])) if result.get('matched_categories') else 'General'
        log_entry = AILog(
            user_id=user_id,
            query_text=message_text,
            intent_extracted='Product Search',
            category_matched=cat_matched,
            results_count=len(result.get('products', []))
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': result.get('message', ''),
        'products': result.get('products', []),
        'matched_categories': result.get('matched_categories', [])
    })

@api_bp.route('/planner/search', methods=['POST', 'GET'])
def planner_search_endpoint():
    if request.method == 'POST':
        data = request.get_json() or {}
        query_text = data.get('query', '')
    else:
        query_text = request.args.get('query', '')

    if not query_text:
        return jsonify({'success': False, 'message': 'Query required.'}), 400

    products, header, matched_cats = match_products_by_intent(query_text)
    
    product_list = [p.to_dict() for p in products]

    return jsonify({
        'success': True,
        'header': header,
        'categories': matched_cats,
        'products': product_list
    })
