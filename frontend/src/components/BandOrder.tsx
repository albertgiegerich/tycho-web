import {
  DndContext,
  DragOverlay,
  closestCenter,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  rectSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import styled from "@emotion/styled";
import { useCallback, useState } from "react";

const RGB_COLORS = ["red", "green", "blue"];

const BandBox = ({ id, color }: { id: string; color?: string }) => (
  <BandBoxContainer color={color}>{id}</BandBoxContainer>
);

const SortableBand = ({ id, color }: { id: string; color?: string }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0 : 1,
      }}
    >
      <BandBox id={id} color={color} />
    </div>
  );
};

interface BandOrderProps {
  onChange: (bands: number[]) => void;
  bandOrder: number[];
}

export const BandOrder = ({ onChange, bandOrder }: BandOrderProps) => {
  const bands = bandOrder.map(String);
  const [activeId, setActiveId] = useState<string | null>(null);

  const onDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(String(event.active.id));
  }, []);

  const onDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (over && active.id !== over.id) {
        const next = arrayMove(
          bands,
          bands.indexOf(String(active.id)),
          bands.indexOf(String(over.id)),
        );
        onChange(next.map(Number));
      }
      setActiveId(null);
    },
    [onChange, bands],
  );

  return (
    <DndContext
      collisionDetection={closestCenter}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <SortableContext items={bands} strategy={rectSortingStrategy}>
        <BandGrid>
          {bands.map((band, i) => (
            <SortableBand key={band} id={band} color={RGB_COLORS[i]} />
          ))}
        </BandGrid>
      </SortableContext>
      <DragOverlay>{activeId ? <BandBox id={activeId} /> : null}</DragOverlay>
    </DndContext>
  );
};

const BandGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
`;

const BandBoxContainer = styled.div<{ color?: string }>`
  padding: 6px 0;
  text-align: center;
  background: ${({ color }) => color ?? "rgba(255, 255, 255, 0.1)"};
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: grab;
  user-select: none;
`;
