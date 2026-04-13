import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from datetime import datetime, timedelta
from database_handler import DatabaseHandler

class FinancialPredictor:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.models = {}
        
    def prepare_features(self, df: pd.DataFrame, forecast_days: int = 7) -> tuple:
        """Prepare features for machine learning"""
        # Create lag features
        for lag in [1, 3, 5, 7]:
            # sift  get past values by moving data down
            df[f'Close_lag_{lag}'] = df['Close'].shift(lag)
            df[f'Volume_lag_{lag}'] = df['Volume'].shift(lag)
        
        # Rolling statistics 
        # rolling(window=7) = look at last 7 values and calculate mean and std
        df['Close_rolling_mean_7'] = df['Close'].rolling(window=7).mean()
        df['Close_rolling_std_7'] = df['Close'].rolling(window=7).std()
        df['Volume_rolling_mean_7'] = df['Volume'].rolling(window=7).mean()
        
        # Technical indicators (if not already present)
        if 'RSI' not in df.columns:
            # Difference between today’s price and yesterday’s price
            delta = df['Close'].diff()
            # Calculate average gain and loss over the past 14 days
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            # Calculate Relative Strength (RS) and Relative Strength Index (RSI)
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        # Target variable: Future close price
        df['Target'] = df['Close'].shift(-forecast_days)
        
        # Drop NaN
        df = df.dropna()
        
        # Feature columns
        feature_cols = [col for col in df.columns if col not in 
                       ['Date', 'Target', 'Ticker', 'Processing_Date']]
        
        return df[feature_cols], df['Target'], df['Date']
    
    def train_model(self, ticker: str):
        """Train prediction model for specific ticker"""
        # Get data from database
        # Fetch stock data for the given ticker from the database
        df = self.db_handler.get_stock_data(ticker)
        
        if len(df) < 50:
            print(f"Not enough data for {ticker}")
            return None
        
        # Prepare features
        X, y, dates = self.prepare_features(df)
        
        if len(X) < 30:
            print(f"Not enough samples for {ticker}")
            return None
        
        # Split data
        X_train, X_test, y_train, y_test, dates_train, dates_test = train_test_split(
            X, y, dates, test_size=0.2, shuffle=False
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        print(f"Model for {ticker} trained:")
        print(f"  MAE: ${mae:.2f}")
        print(f"  RMSE: ${rmse:.2f}")
        
        # Save model and scaler
        self.models[ticker] = {
            'model': model,
            'scaler': scaler,
            'feature_names': X.columns.tolist(),
            'metrics': {'MAE': mae, 'RMSE': rmse}
        }
        
        # Save to file
        # Save trained model and scaler to disk for later use (no need to retrain)
        joblib.dump(model, f'models/{ticker}_model.pkl')
        joblib.dump(scaler, f'models/{ticker}_scaler.pkl')
        
        return self.models[ticker]
    
    
    def predict_future(self, ticker: str, days_ahead: int = 7):
        """Predict future prices"""
        if ticker not in self.models:
            print(f"Training model for {ticker} first...")
            self.train_model(ticker)
        
        # Get latest data
        df = self.db_handler.get_stock_data(ticker)
        
        if len(df) < 50:
            return None
        
        # Prepare features for prediction
        X, _, _ = self.prepare_features(df, forecast_days=days_ahead)
        
        if len(X) == 0:
            return None
        
        # Use the latest data point for prediction
        latest_features = X.iloc[[-1]]
        
        # Scale features
        scaler = self.models[ticker]['scaler']
        latest_features_scaled = scaler.transform(latest_features)
        
        # Make prediction
        model = self.models[ticker]['model']
        prediction = model.predict(latest_features_scaled)[0]
        
        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': self.models[ticker]['feature_names'],
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Calculate confidence interval (simplified)
        y_pred_all = model.predict(scaler.transform(X))
        residuals = df['Close'].iloc[-len(y_pred_all):].values - y_pred_all
        std_residuals = np.std(residuals)
        
        ci_lower = prediction - 1.96 * std_residuals
        ci_upper = prediction + 1.96 * std_residuals
        
        result = {
            'ticker': ticker,
            'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
            'predicted_close': float(prediction),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'current_price': float(df['Close'].iloc[-1]),
            'expected_return': float((prediction - df['Close'].iloc[-1]) / df['Close'].iloc[-1] * 100),
            'feature_importance': feature_importance.head(10).to_dict('records'),
            'model_metrics': self.models[ticker]['metrics']
        }
        
        # Save prediction to database
        self.db_handler.save_prediction(result)
        
        return result
    
    def generate_trading_signals(self, ticker: str):
        """Generate trading signals based on predictions"""
        prediction = self.predict_future(ticker)
        
        if not prediction:
            return None
        
        current_price = prediction['current_price']
        predicted_price = prediction['predicted_close']
        
        # Simple signal logic
        price_change_pct = prediction['expected_return']
        
        if price_change_pct > 5:
            signal = "STRONG BUY"
            confidence = "HIGH"
        elif price_change_pct > 2:
            signal = "BUY"
            confidence = "MEDIUM"
        elif price_change_pct < -5:
            signal = "STRONG SELL"
            confidence = "HIGH"
        elif price_change_pct < -2:
            signal = "SELL"
            confidence = "MEDIUM"
        else:
            signal = "HOLD"
            confidence = "LOW"
        
        return {
            'ticker': ticker,
            'signal': signal,
            'confidence': confidence,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'expected_return_pct': price_change_pct,
            'timestamp': datetime.now().isoformat()
        }