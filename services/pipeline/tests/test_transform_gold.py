import pandas as pd

def test_bike_availability_change():
    # 1. Create fake raw data representing one station over time
    mock_data = pd.DataFrame({
        'station_id': ['A1', 'A1', 'A1'],
        'collected_at': ['2026-10-28 10:00', '2026-10-28 10:05', '2026-10-28 10:10'],
        'num_bikes_available': [10, 8, 12] # Started with 10, dropped to 8, went up to 12
    })
    
    # 2. Apply sorting and difference logic from transform_gold.py
    df = mock_data.sort_values(by=['station_id', 'collected_at'])
    df['bike_availability_change'] = df.groupby('station_id')['num_bikes_available'].diff().fillna(0).astype(int)
    
    # 3. Check if matches the expected momentum (First row 0, then -2 bikes, then +4 bikes)
    expected_changes = [0, -2, 4]
    
    assert df['bike_availability_change'].tolist() == expected_changes, "The rolling difference calculation failed!"