import { useMemo, useState } from "react";

/**
 * Official TradingView Single Ticker via iframe embed (no API key).
 * Symbol changes remount the iframe so the panel quote updates with selection.
 * Does not scrape widget data — TradingView renders its own market feed inside the iframe.
 */
export function TradingViewTicker({
  symbol,
  currency,
}: {
  symbol: string;
  currency?: string | null;
}) {
  const [failed, setFailed] = useState(false);

  const src = useMemo(() => {
    const opts = {
      symbol,
      width: 350,
      colorTheme: "dark",
      isTransparent: true,
      locale: "kr",
    };
    // Official Single Ticker embed path is `single-quote` (TradingView naming).
    return `https://s.tradingview.com/embed-widget/single-quote/?locale=kr&symbol=${encodeURIComponent(symbol)}#${encodeURIComponent(JSON.stringify(opts))}`;
  }, [symbol]);

  if (failed) {
    return <p className="muted-line">주가 조회 불가</p>;
  }

  return (
    <div className="tv-quote">
      <div className="tv-quote-host">
        <iframe
          key={symbol}
          title={`${symbol} 주가`}
          src={src}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          onError={() => setFailed(true)}
          onLoad={(e) => {
            // Empty/error frames from TradingView sometimes still fire load; leave visible.
            void e;
          }}
        />
      </div>
      <p className="fine">
        TradingView Single Ticker · {symbol}
        {currency ? ` · ${currency}` : ""}
        . 시세가 지연될 수 있으며, 장 마감 후에는 확인 가능한 마지막 거래가가 표시됩니다.
      </p>
    </div>
  );
}
