import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; onRetry?: () => void };
type State = { error: Error | null; key: number };

/**
 * Isolates canvas/renderer failures from the app shell so navigation/panels stay usable.
 */
export class MapErrorBoundary extends Component<Props, State> {
  state: State = { error: null, key: 0 };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[MapErrorBoundary]", error, info.componentStack);
  }

  retry = () => {
    this.props.onRetry?.();
    this.setState((s) => ({ error: null, key: s.key + 1 }));
  };

  render() {
    if (this.state.error) {
      return (
        <div className="map-error" role="alert">
          <p className="map-error-t">맵 렌더링 오류</p>
          <p className="map-error-m">
            그래프 표시 중 문제가 발생했습니다. 앱 메뉴와 패널은 계속 사용할 수 있습니다.
          </p>
          <p className="fine num">{this.state.error.message || "unknown"}</p>
          <button type="button" className="pfb-more" onClick={this.retry}>맵 다시 시도</button>
        </div>
      );
    }
    return <div key={this.state.key} className="map-boundary">{this.props.children}</div>;
  }
}
