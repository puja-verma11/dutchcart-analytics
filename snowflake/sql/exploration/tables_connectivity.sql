Select count(*)  as all_rows, 
count(DISTINCT Record : order_id :: string) As unique_order_ids 
from orders 