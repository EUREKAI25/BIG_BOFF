"""
SCRIPT À EXÉCUTER LOCALEMENT
Phase A - Mesure du momentum réel sur Binance

Installation requise:
pip install requests pandas numpy matplotlib

Exécution:
python analyze_binance_momentum.py

Ce script va:
1. Récupérer les 10 paires les plus liquides sur Binance
2. Analyser le momentum sur 1m, 5m, 15m, 1h
3. Identifier les meilleures opportunités
4. Générer des graphiques
"""

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

class BinanceMomentumAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        
    def get_top_pairs(self, limit=10):
        """Récupère les paires les plus liquides (volume 24h)"""
        print("📈 Récupération des paires les plus liquides...")
        url = f"{self.base_url}/ticker/24hr"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Filtrer les paires USDT et trier par volume
            usdt_pairs = [
                d for d in data 
                if d['symbol'].endswith('USDT') and 
                not any(x in d['symbol'] for x in ['UP', 'DOWN', 'BEAR', 'BULL'])
            ]
            
            # Trier par volume en USDT
            sorted_pairs = sorted(
                usdt_pairs, 
                key=lambda x: float(x['quoteVolume']), 
                reverse=True
            )
            
            top = [p['symbol'] for p in sorted_pairs[:limit]]
            print(f"✓ {len(top)} paires sélectionnées: {', '.join(top)}")
            return top
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            # Fallback sur paires connues
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 
                    'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'LTCUSDT']
    
    def get_klines(self, symbol, interval='5m', limit=1000):
        """
        Récupère les bougies (klines) historiques
        interval: '1m', '5m', '15m', '1h', '4h', '1d'
        """
        url = f"{self.base_url}/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, dict) and 'code' in data:
                print(f"  ❌ Erreur API pour {symbol}: {data.get('msg', 'Unknown')}")
                return None
            
            # Convertir en DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convertir en types appropriés
            df['open'] = df['open'].astype(float)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculer si bougie verte (1) ou rouge (0)
            df['is_green'] = (df['close'] > df['open']).astype(int)
            
            return df
            
        except Exception as e:
            print(f"  ❌ Erreur pour {symbol} {interval}: {e}")
            return None
    
    def calculate_momentum(self, df, streak_length=2):
        """
        Calcule le momentum: probabilité de continuation après N bougies de même couleur
        """
        if df is None or len(df) < streak_length + 1:
            return None
        
        results = {
            'green_streaks_found': 0,
            'green_continued': 0,
            'red_streaks_found': 0,
            'red_continued': 0
        }
        
        for i in range(streak_length, len(df)):
            prev_candles = df.iloc[i-streak_length:i]['is_green'].values
            current_candle = df.iloc[i]['is_green']
            
            # Si N bougies vertes consécutives
            if np.all(prev_candles == 1):
                results['green_streaks_found'] += 1
                if current_candle == 1:
                    results['green_continued'] += 1
            
            # Si N bougies rouges consécutives
            elif np.all(prev_candles == 0):
                results['red_streaks_found'] += 1
                if current_candle == 0:
                    results['red_continued'] += 1
        
        # Calculer les probabilités
        prob_green = (results['green_continued'] / results['green_streaks_found'] 
                     if results['green_streaks_found'] > 0 else 0)
        prob_red = (results['red_continued'] / results['red_streaks_found'] 
                   if results['red_streaks_found'] > 0 else 0)
        
        return {
            'prob_green_after_greens': prob_green,
            'prob_red_after_reds': prob_red,
            'momentum_green': prob_green - 0.5,
            'momentum_red': prob_red - 0.5,
            'momentum_avg': ((prob_green - 0.5) + (prob_red - 0.5)) / 2,
            **results
        }
    
    def analyze_pair(self, symbol, intervals=['1m', '5m', '15m', '1h'], limit=1000):
        """Analyse une paire sur plusieurs timeframes"""
        print(f"\n📊 {symbol}:")
        results = {}
        
        for interval in intervals:
            print(f"  {interval}...", end=" ", flush=True)
            df = self.get_klines(symbol, interval, limit)
            
            if df is not None:
                momentum = self.calculate_momentum(df, streak_length=2)
                if momentum:
                    results[interval] = momentum
                    print(f"✓ Momentum: {momentum['momentum_avg']*100:+.2f}%")
                else:
                    print("⚠️ Pas assez de données")
            else:
                print("❌ Erreur")
            
            time.sleep(0.2)  # Rate limiting
        
        return results

# ==================== EXÉCUTION ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 ANALYSE DU MOMENTUM RÉEL SUR BINANCE")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    analyzer = BinanceMomentumAnalyzer()
    
    # 1. Récupérer les top paires
    top_pairs = analyzer.get_top_pairs(limit=10)
    
    # 2. Analyser chaque paire
    all_results = {}
    intervals = ['1m', '5m', '15m', '1h']
    
    for symbol in top_pairs:
        results = analyzer.analyze_pair(symbol, intervals)
        all_results[symbol] = results
        time.sleep(0.5)  # Rate limiting entre paires
    
    # 3. Synthèse globale
    print("\n" + "=" * 70)
    print("📊 SYNTHÈSE GLOBALE DU MOMENTUM")
    print("=" * 70)
    
    summary = []
    for symbol, intervals_data in all_results.items():
        for interval, data in intervals_data.items():
            summary.append({
                'Paire': symbol,
                'Timeframe': interval,
                'Momentum (%)': data['momentum_avg'] * 100,
                'P(Vert|2Verts) (%)': data['prob_green_after_greens'] * 100,
                'P(Rouge|2Rouges) (%)': data['prob_red_after_reds'] * 100,
                'N_streaks_verts': data['green_streaks_found'],
                'N_streaks_rouges': data['red_streaks_found']
            })
    
    df_summary = pd.DataFrame(summary)
    
    if len(df_summary) > 0:
        # Trier par momentum moyen décroissant
        df_summary = df_summary.sort_values('Momentum (%)', ascending=False)
        
        print("\n🏆 TOP 15 - Plus fort momentum:")
        print(df_summary.head(15).to_string(index=False))
        
        print("\n💡 Moyenne par timeframe:")
        avg_by_interval = df_summary.groupby('Timeframe')['Momentum (%)'].agg(['mean', 'std', 'count'])
        print(avg_by_interval.to_string())
        
        print("\n💡 Moyenne par paire:")
        avg_by_pair = df_summary.groupby('Paire')['Momentum (%)'].agg(['mean', 'std', 'count'])
        print(avg_by_pair.sort_values('mean', ascending=False).head(10).to_string())
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'binance_momentum_analysis_{timestamp}.csv'
        df_summary.to_csv(filename, index=False)
        print(f"\n✓ Résultats sauvegardés: {filename}")
        
        # Graphiques
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Distribution du momentum
            axes[0, 0].hist(df_summary['Momentum (%)'], bins=30, edgecolor='black', alpha=0.7)
            axes[0, 0].axvline(5.0, color='red', linestyle='--', label='Cible: 5%')
            axes[0, 0].set_xlabel('Momentum (%)')
            axes[0, 0].set_ylabel('Fréquence')
            axes[0, 0].set_title('Distribution du Momentum')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. Momentum par timeframe
            avg_by_interval_plot = df_summary.groupby('Timeframe')['Momentum (%)'].mean().sort_values()
            avg_by_interval_plot.plot(kind='barh', ax=axes[0, 1], color='steelblue')
            axes[0, 1].axvline(5.0, color='red', linestyle='--', label='Cible: 5%')
            axes[0, 1].set_xlabel('Momentum moyen (%)')
            axes[0, 1].set_title('Momentum par Timeframe')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Top 10 paires
            top10 = df_summary.groupby('Paire')['Momentum (%)'].mean().nlargest(10).sort_values()
            top10.plot(kind='barh', ax=axes[1, 0], color='green')
            axes[1, 0].axvline(5.0, color='red', linestyle='--', label='Cible: 5%')
            axes[1, 0].set_xlabel('Momentum moyen (%)')
            axes[1, 0].set_title('Top 10 Paires par Momentum')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # 4. Scatter: P(Vert|2Verts) vs P(Rouge|2Rouges)
            axes[1, 1].scatter(
                df_summary['P(Vert|2Verts) (%)'], 
                df_summary['P(Rouge|2Rouges) (%)'],
                alpha=0.5
            )
            axes[1, 1].axhline(50, color='gray', linestyle='--', alpha=0.5)
            axes[1, 1].axvline(50, color='gray', linestyle='--', alpha=0.5)
            axes[1, 1].set_xlabel('P(Vert|2Verts) (%)')
            axes[1, 1].set_ylabel('P(Rouge|2Rouges) (%)')
            axes[1, 1].set_title('Corrélation Probabilités')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            graph_filename = f'binance_momentum_graphs_{timestamp}.png'
            plt.savefig(graph_filename, dpi=150, bbox_inches='tight')
            print(f"✓ Graphiques sauvegardés: {graph_filename}")
            
        except Exception as e:
            print(f"⚠️ Impossible de générer les graphiques: {e}")
        
        # Conclusion
        print("\n" + "=" * 70)
        print("🎯 CONCLUSION")
        print("=" * 70)
        
        momentum_global = df_summary['Momentum (%)'].mean()
        momentum_max = df_summary['Momentum (%)'].max()
        momentum_min = df_summary['Momentum (%)'].min()
        
        print(f"""
Momentum moyen global: {momentum_global:.2f}%
Momentum maximum: {momentum_max:.2f}%
Momentum minimum: {momentum_min:.2f}%

🎯 Pour obtenir +6,3€, il faut un momentum ≥ 5%
   → Nombre de cas avec momentum ≥ 5%: {len(df_summary[df_summary['Momentum (%)'] >= 5])}
   → Pourcentage des cas: {len(df_summary[df_summary['Momentum (%)'] >= 5]) / len(df_summary) * 100:.1f}%

{'✅ OPPORTUNITÉS DÉTECTÉES' if momentum_max >= 5 else '⚠️ MOMENTUM INSUFFISANT'}

📝 Prochaine étape: 
   Phase B - Backtest sur les meilleures paires identifiées
   (avec FRAIS Binance inclus: 0.1% par trade minimum)
        """)
    
    else:
        print("\n❌ Aucune donnée récupérée. Vérifier la connexion internet.")

    print("\n" + "=" * 70)
    print("✅ Analyse terminée")
    print("=" * 70)
