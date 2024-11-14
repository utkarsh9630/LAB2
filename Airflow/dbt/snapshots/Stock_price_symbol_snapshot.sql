{% snapshot snapshot_session_summary %}

{{
  config(
    target_schema='snapshot',
    unique_key='date_symbol',
    strategy='timestamp',
    updated_at='last_updated_timestamp',
    invalidate_hard_deletes=True
  )
}}

SELECT * FROM {{ ref('moving_averages') }}

{% endsnapshot %}