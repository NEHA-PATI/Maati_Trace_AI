import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { getHistory } from "@/features/crop-observation/api/cropObservationApi";
import HistoryTimeline from "@/features/crop-observation/components/HistoryTimeline";
import MobileScreen from "@/features/crop-observation/components/MobileScreen";
import { HistorySkeleton } from "@/features/crop-observation/components/Skeletons";
import { useLocale } from "@/features/crop-observation/hooks/useLocale";
import { STRINGS, primary } from "@/features/crop-observation/i18n";

export default function ObservationHistoryPage() {
  const { cropCycleId } = useParams();
  const navigate = useNavigate();
  const [locale] = useLocale();

  const [items, setItems] = useState([]);
  const [nextCursor, setNextCursor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const loadFirstPage = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const page = await getHistory(cropCycleId, { limit: 20 });
      setItems(page.items);
      setNextCursor(page.next_cursor);
    } catch (err) {
      setError(err?.message || "Could not load history.");
    } finally {
      setLoading(false);
    }
  }, [cropCycleId]);

  useEffect(() => {
    loadFirstPage();
  }, [loadFirstPage]);

  async function loadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    try {
      const page = await getHistory(cropCycleId, { before: nextCursor, limit: 20 });
      setItems((prev) => [...prev, ...page.items]);
      setNextCursor(page.next_cursor);
    } catch (err) {
      setError(err?.message || "Could not load more.");
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <MobileScreen
      onBack={() => navigate(-1)}
      title={primary(STRINGS.history, locale)}
      subtitle={locale === "or-IN" ? "Previous Updates" : "ପୂର୍ବ ତଥ୍ୟ"}
    >
      {error ? (
        <p className="mb-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      ) : null}

      {loading ? <HistorySkeleton /> : <HistoryTimeline items={items} locale={locale} />}

      {nextCursor ? (
        <div className="pt-5">
          <Button variant="outline" className="h-11 w-full" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? primary(STRINGS.saving, locale) : primary(STRINGS.loadMore, locale)}
          </Button>
        </div>
      ) : null}
    </MobileScreen>
  );
}
