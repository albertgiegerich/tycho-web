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

const BandBox = ({ id }: { id: string }) => (
  <BandBoxContainer>{id}</BandBoxContainer>
);

const SortableBand = ({ id }: { id: string }) => {
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
      <BandBox id={id} />
    </div>
  );
};

export const BandOrder = () => {
  const [bands, setBands] = useState(["1", "2", "3", "4", "5", "6"]);
  const [activeId, setActiveId] = useState<string | null>(null);

  const onDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(String(event.active.id));
  }, []);

  const onDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setBands((prev) => {
        const oldIndex = prev.indexOf(String(active.id));
        const newIndex = prev.indexOf(String(over.id));
        return arrayMove(prev, oldIndex, newIndex);
      });
    }
    setActiveId(null);
  }, []);

  return (
    <DndContext
      collisionDetection={closestCenter}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <SortableContext items={bands} strategy={rectSortingStrategy}>
        <BandGrid>
          {bands.map((band) => (
            <SortableBand key={band} id={band} />
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

const BandBoxContainer = styled.div`
  padding: 6px 0;
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: grab;
  user-select: none;
`;
