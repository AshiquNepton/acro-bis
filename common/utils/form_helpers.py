# common/utils/form_helpers.py
"""
Common utility functions for form handling and database operations
"""

from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import connection
from django.db.models import Q
from common.middleware.database_middleware import get_customer_db
import logging

logger = logging.getLogger(__name__)


def fetch_record_by_field(model_class, field_name, field_value, database=None):
    """
    Generic function to fetch a record by any field and return its data
    
    Args:
        model_class: Django model class (e.g., Organization)
        field_name: Field name to search by (e.g., 'CompanyId', 'Email')
        field_value: Value to search for
        database: Database alias to use (defaults to customer_db)
        
    Returns:
        dict: {'success': bool, 'data': dict or None, 'error': str or None}
    
    Example:
        result = fetch_record_by_field(Organization, 'CompanyId', 1)
        if result['success']:
            company_data = result['data']
    """
    
    try:
        # Use provided database or get customer database
        db = database or get_customer_db()
        
        # Validate field exists
        if not hasattr(model_class, field_name):
            return {
                'success': False,
                'data': None,
                'error': f'Field "{field_name}" does not exist in {model_class.__name__}'
            }
        
        # Build query filter
        filter_kwargs = {field_name: field_value}
        
        # Query with optimization (select all fields at once)
        queryset = model_class.objects.using(db).filter(**filter_kwargs)
        
        # Check if record exists
        if not queryset.exists():
            return {
                'success': False,
                'data': None,
                'error': f'No record found with {field_name}={field_value}'
            }
        
        # Get the record
        try:
            record = queryset.first()
        except MultipleObjectsReturned:
            logger.warning(f'Multiple records found for {field_name}={field_value}, returning first')
            record = queryset.first()
        
        # Convert model instance to dictionary
        data = model_to_dict_with_dates(record)
        
        return {
            'success': True,
            'data': data,
            'error': None
        }
        
    except ObjectDoesNotExist:
        return {
            'success': False,
            'data': None,
            'error': f'Record not found'
        }
    except Exception as e:
        logger.error(f'Error fetching record: {str(e)}', exc_info=True)
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


def search_records_by_field(model_class, field_name, search_term, database=None, limit=10):
    """
    Search for records where field contains the search term (case-insensitive)
    
    Args:
        model_class: Django model class
        field_name: Field name to search in
        search_term: Text to search for
        database: Database alias to use
        limit: Maximum number of results to return
        
    Returns:
        dict: {'success': bool, 'results': list, 'count': int, 'error': str or None}
        
    Example:
        result = search_records_by_field(Organization, 'CompanyName', 'Nep')
        # Returns companies with names containing 'Nep' (Neptune, Nepton, etc.)
    """
    
    try:
        # Use provided database or get customer database
        db = database or get_customer_db()
        
        # Validate field exists
        if not hasattr(model_class, field_name):
            return {
                'success': False,
                'results': [],
                'count': 0,
                'error': f'Field "{field_name}" does not exist in {model_class.__name__}'
            }
        
        # Don't search for empty strings
        if not search_term or not search_term.strip():
            return {
                'success': True,
                'results': [],
                'count': 0,
                'error': None
            }
        
        # Build case-insensitive search query
        filter_kwargs = {f'{field_name}__icontains': search_term}
        
        # Query with limit
        queryset = model_class.objects.using(db).filter(**filter_kwargs)[:limit]
        
        # Convert to list of dictionaries
        results = []
        for record in queryset:
            record_dict = model_to_dict_with_dates(record)
            results.append(record_dict)
        
        return {
            'success': True,
            'results': results,
            'count': len(results),
            'error': None
        }
        
    except Exception as e:
        logger.error(f'Error searching records: {str(e)}', exc_info=True)
        return {
            'success': False,
            'results': [],
            'count': 0,
            'error': str(e)
        }


def search_records_multi_field(model_class, search_fields, search_term, database=None, limit=10):
    """
    Search for records across multiple fields (OR search)
    
    Args:
        model_class: Django model class
        search_fields: List of field names to search in
        search_term: Text to search for
        database: Database alias to use
        limit: Maximum number of results
        
    Returns:
        dict: {'success': bool, 'results': list, 'count': int, 'error': str or None}
        
    Example:
        # Search in both company name and email
        result = search_records_multi_field(
            Organization, 
            ['CompanyName', 'Email'], 
            'test'
        )
    """
    
    try:
        db = database or get_customer_db()
        
        if not search_term or not search_term.strip():
            return {
                'success': True,
                'results': [],
                'count': 0,
                'error': None
            }
        
        # Build OR query
        q_objects = Q()
        for field_name in search_fields:
            if hasattr(model_class, field_name):
                q_objects |= Q(**{f'{field_name}__icontains': search_term})
        
        # Execute query
        queryset = model_class.objects.using(db).filter(q_objects).distinct()[:limit]
        
        # Convert to list
        results = []
        for record in queryset:
            record_dict = model_to_dict_with_dates(record)
            results.append(record_dict)
        
        return {
            'success': True,
            'results': results,
            'count': len(results),
            'error': None
        }
        
    except Exception as e:
        logger.error(f'Error in multi-field search: {str(e)}', exc_info=True)
        return {
            'success': False,
            'results': [],
            'count': 0,
            'error': str(e)
        }


def model_to_dict_with_dates(record):
    """
    Convert model instance to dictionary with proper date/datetime handling
    
    Args:
        record: Django model instance
        
    Returns:
        dict: Model data with properly formatted dates
    """
    data = {}
    for field in record._meta.fields:
        field_name = field.name
        value = getattr(record, field_name)
        
        # Handle special field types
        if value is None:
            data[field_name] = None
        elif hasattr(value, 'strftime'):  # Date/DateTime fields
            data[field_name] = value.strftime('%Y-%m-%d')
        elif isinstance(value, bool):
            data[field_name] = value
        else:
            data[field_name] = str(value)
    
    return data


def fetch_record_by_field_view(request, model_class, field_mapping=None):
    """
    Django view function to fetch a record by field via AJAX
    
    Args:
        request: Django request object
        model_class: Django model class
        field_mapping: Optional dict to map database fields to frontend fields
        
    Returns:
        JsonResponse with record data
    """
    
    try:
        # Get search parameters
        field_name = request.GET.get('field')
        field_value = request.GET.get('value')
        
        if not field_name or not field_value:
            return JsonResponse({
                'success': False,
                'error': 'Missing field or value parameter'
            })
        
        # Fetch record
        result = fetch_record_by_field(model_class, field_name, field_value)
        
        if result['success'] and result['data'] and field_mapping:
            # Apply field mapping if provided
            mapped_data = {}
            for db_field, frontend_field in field_mapping.items():
                if db_field in result['data']:
                    mapped_data[frontend_field] = result['data'][db_field]
            result['data'] = mapped_data
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f'Error in fetch_record_by_field_view: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def search_records_view(request, model_class, field_name, field_mapping=None, display_fields=None):
    """
    Django view function for autocomplete search via AJAX
    
    Args:
        request: Django request object
        model_class: Django model class
        field_name: Field name to search in
        field_mapping: Optional dict to map database fields to frontend fields
        display_fields: List of fields to include in dropdown display
        
    Returns:
        JsonResponse with search results
        
    Example:
        GET /company/search/?q=Nep&limit=10
    """
    
    try:
        search_term = request.GET.get('q', '')
        limit = int(request.GET.get('limit', 10))
        
        # Perform search
        result = search_records_by_field(model_class, field_name, search_term, limit=limit)
        
        if result['success'] and field_mapping:
            # Apply field mapping to all results
            mapped_results = []
            for record_data in result['results']:
                mapped_record = {}
                for db_field, frontend_field in field_mapping.items():
                    if db_field in record_data:
                        mapped_record[frontend_field] = record_data[db_field]
                
                # Add display text for dropdown
                if display_fields:
                    display_parts = []
                    for display_field in display_fields:
                        if display_field in mapped_record and mapped_record[display_field]:
                            display_parts.append(str(mapped_record[display_field]))
                    mapped_record['_display'] = ' - '.join(display_parts)
                
                mapped_results.append(mapped_record)
            
            result['results'] = mapped_results
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f'Error in search_records_view: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'results': [],
            'count': 0,
            'error': str(e)
        })


def optimize_query(queryset):
    """
    Optimize a queryset by adding select_related and prefetch_related
    based on the model's foreign keys and many-to-many relationships
    """
    model = queryset.model
    
    # Get all foreign key fields
    fk_fields = [
        f.name for f in model._meta.get_fields()
        if f.many_to_one and f.concrete
    ]
    
    # Get all many-to-many fields
    m2m_fields = [
        f.name for f in model._meta.get_fields()
        if f.many_to_many and not f.auto_created
    ]
    
    # Apply optimizations
    if fk_fields:
        queryset = queryset.select_related(*fk_fields)
    
    if m2m_fields:
        queryset = queryset.prefetch_related(*m2m_fields)
    
    return queryset


def get_database_connection_info():
    """Get current database connection information for debugging"""
    db = get_customer_db()
    db_settings = connection.settings_dict
    
    return {
        'database': db,
        'engine': db_settings.get('ENGINE', 'Unknown'),
        'name': db_settings.get('NAME', 'Unknown'),
        'host': db_settings.get('HOST', 'Unknown'),
        'port': db_settings.get('PORT', 'Unknown'),
    }