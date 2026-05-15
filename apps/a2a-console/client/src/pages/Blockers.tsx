import { Link } from 'react-router-dom';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Button } from '@/components/ui/button';
import { BlockerCard } from '@/components/BlockerCard';
import { useActiveTask } from '@/hooks/useActiveTask';
import { useBlockers } from '@/hooks/useBlockers';

export default function BlockersPage() {
  const { data: active } = useActiveTask();
  const taskId = active?.active_task_id ?? null;
  const { data } = useBlockers(taskId);

  return (
    <div className="px-5 py-5">
      <Card>
        <CardHeader>
          <CardTitle>当前 Blocker（active task）</CardTitle>
        </CardHeader>
        <CardContent>
          {!taskId ? (
            <Empty title="无 active task" action={<Button asChild size="sm"><Link to="/tasks">查看 Tasks</Link></Button>} />
          ) : !data || data.items.length === 0 ? (
            <Empty title="无 active blocker" />
          ) : (
            <div className="space-y-3">
              {data.items.map((b) => <BlockerCard key={b.blocker_id ?? b.file_path} blocker={b} />)}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
