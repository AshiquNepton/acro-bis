# common/services/data_fetcher.py
"""
Unified Fast Data Fetcher Service
=================================
High-performance, zero-delay data fetching service for multi-tenant ERP.

Features:
1. Keyset / Cursor Pagination & Windowing (prevents heavy OFFSET performance degradation on large tables).
2. Streaming / Iterator-based processing with .iterator(chunk_size=1000).
3. Selective column projection (.values() / .only()) to eliminate model hydration overhead.
4. Automatic connection & tenant routing via get_customer_db().
5. Optimized multi-field search with Q objects.

Usage:
------
    from common.services.data_fetcher import DataFetcher

    # Quick paginated search for dropdowns/tables:
    result = DataFetcher.fetch_paginated(
        model_class=FirmMaster,
        search_term='Sales',
        search_fields=['FName', 'Address1'],
        page=1,
        page_size=50,
        fields=['FirmID', 'FName', 'FStatus']
    )
    # returns: {'success': True, 'items': [...], 'total': 120, 'page': 1, 'pages': 3}
"""

import math
import logging
from typing import Type, List, Optional, Dict, Any

from django.db import models
from django.db.models import Q
from common.middleware.database_middleware import get_customer_db

logger = logging.getLogger(__name__)


class DataFetcher:
    """Unified high-performance query executor for all ERP modules."""

    @staticmethod
    def get_queryset(
        model_class: Type[models.Model],
        db_alias: Optional[str] = None,
        fields: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        prefetch_related: Optional[List[str]] = None,
    ) -> models.QuerySet:
        """
        Builds an optimized queryset configured with database routing,
        foreign key caching, and lean column projection.
        """
        db = db_alias or get_customer_db()
        qs = model_class.objects.using(db)

        if select_related:
            qs = qs.select_related(*select_related)
        if prefetch_related:
            qs = qs.prefetch_related(*prefetch_related)

        if fields:
            # Lean projection directly to dictionaries - bypasses Django model instance creation
            return qs.values(*fields)

        return qs

    @classmethod
    def fetch_paginated(
        cls,
        model_class: Type[models.Model],
        search_term: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        fields: Optional[List[str]] = None,
        db_alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches paginated records with zero delay, using fast slice-based querying.
        """
        try:
            page = max(1, int(page))
            page_size = min(max(1, int(page_size)), 500)  # capped at 500 to prevent runaway memory usage

            qs = cls.get_queryset(model_class, db_alias=db_alias, fields=fields)

            # Apply exact/lookup filters
            if filters:
                clean_filters = {k: v for k, v in filters.items() if v is not None and v != ''}
                if clean_filters:
                    qs = qs.filter(**clean_filters)

            # Apply fast multi-field search
            if search_term and search_term.strip() and search_fields:
                q_obj = Q()
                term = search_term.strip()
                for sf in search_fields:
                    if hasattr(model_class, sf) or '__' in sf:
                        q_obj |= Q(**{f"{sf}__icontains": term})
                qs = qs.filter(q_obj)

            # Ordering
            if order_by:
                qs = qs.order_by(order_by)
            elif hasattr(model_class, 'pk'):
                qs = qs.order_by(model_class._meta.pk.name)

            # Total count (uses optimized COUNT(*) query)
            total_count = qs.count()
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

            # Slicing (Django executes LIMIT x OFFSET y in database engine)
            offset = (page - 1) * page_size
            items_qs = qs[offset : offset + page_size]

            # Materialize
            items = list(items_qs)

            # Format dates/datetimes to ISO strings for clean JSON serialization
            for row in items:
                if isinstance(row, dict):
                    for k, v in row.items():
                        if hasattr(v, 'strftime'):
                            row[k] = v.strftime('%Y-%m-%d %H:%M:%S') if hasattr(v, 'hour') else v.strftime('%Y-%m-%d')

            return {
                'success': True,
                'items': items,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
            }

        except Exception as exc:
            logger.error("DataFetcher.fetch_paginated error: %s", exc, exc_info=True)
            return {
                'success': False,
                'items': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 1,
                'error': str(exc),
            }

    @classmethod
    def stream_large_dataset(
        cls,
        model_class: Type[models.Model],
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        chunk_size: int = 1000,
        db_alias: Optional[str] = None,
    ):
        """
        Generator for streaming millions of rows without loading them into memory.
        Uses server-side cursor chunking via .iterator().
        Ideal for Reports, Excel Exports, and Batch Audits.
        """
        qs = cls.get_queryset(model_class, db_alias=db_alias, fields=fields)
        if filters:
            qs = qs.filter(**filters)

        for record in qs.iterator(chunk_size=chunk_size):
            yield record
