import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { BlockerCard } from '@/components/BlockerCard';
import { Badge } from '@/components/ui/badge';
import { useBlockers, useReviews } from '@/hooks/useBlockers';
import { formatTime } from '@/lib/format';

export default function Risk({ taskId }: { taskId: string }) {
  const { data: blockers } = useBlockers(taskId);
  const { data: reviews } = useReviews(taskId);

  return (
    <div className="space-y-4 px-5 py-5">
      <Card>
        <CardHeader>
          <CardTitle>当前 Blocker</CardTitle>
        </CardHeader>
        <CardContent>
          {!blockers || blockers.items.length === 0 ? (
            <Empty title="无 active blocker" description="一切顺利。" />
          ) : (
            <div className="space-y-3">
              {blockers.items.map((b) => (
                <BlockerCard key={b.blocker_id ?? b.file_path} blocker={b} />
              ))}
              {blockers.blockers_history.length > 0 ? (
                <div className="rounded-md bg-muted/40 p-3 text-xs text-muted-foreground">
                  历史 blocker：{blockers.blockers_history.join(', ')}
                </div>
              ) : null}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Human Review 记录</CardTitle>
        </CardHeader>
        <CardContent>
          {!reviews || reviews.items.length === 0 ? (
            <Empty title="还没有 review 记录" />
          ) : (
            <ul className="space-y-2 text-sm">
              {reviews.items.map((r) => (
                <li
                  key={r.review_id ?? r.file_path}
                  className="rounded-md border border-border bg-card p-3"
                >
                  <div className="mb-1 flex flex-wrap items-baseline gap-2">
                    <span className="font-medium">{r.review_type ?? r.review_id ?? 'review'}</span>
                    <Badge
                      variant={
                        r.verdict === 'approved'
                          ? 'default'
                          : r.verdict === 'rejected'
                            ? 'destructive'
                            : 'secondary'
                      }
                      className="text-[10px]"
                    >
                      {r.verdict ?? '—'}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">
                      by {r.reviewer ?? '—'} · {formatTime(r.reviewed_at)}
                    </span>
                  </div>
                  {r.notes ? <p className="text-xs text-muted-foreground">{r.notes}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
