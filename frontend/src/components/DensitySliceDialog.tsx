import { useCallback, useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import TextField from "@mui/material/TextField";

const FLOAT_REGEX = /^-?\d*\.?\d*$/;

interface DensitySliceDialogProps {
  open: boolean;
  onClose: () => void;
  onApply: (breaks: number[]) => void;
}

const DensitySliceDialog = ({
  open,
  onClose,
  onApply,
}: DensitySliceDialogProps) => {
  const [breaks, setBreaks] = useState<string[]>([""]);

  const handleClose = useCallback(() => {
    setBreaks([""]);
    onClose();
  }, [onClose]);

  const handleChange = useCallback((index: number, newValue: string) => {
    if (FLOAT_REGEX.test(newValue)) {
      setBreaks((prev) => {
        const copy = [...prev];
        copy[index] = newValue;
        return copy;
      });
    }
  }, []);

  const handleAdd = useCallback(() => setBreaks((prev) => [...prev, ""]), []);

  const handleRemove = useCallback(
    (index: number) => setBreaks((prev) => prev.filter((_, i) => i !== index)),
    [],
  );

  const handleApply = useCallback(() => {
    const parsed = breaks.map(Number);
    onApply(parsed);
    handleClose();
  }, [breaks, onApply, handleClose]);

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>Density Slice</DialogTitle>
      <DialogContent>
        {breaks.map((b, i) => (
          <Box
            key={i}
            sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
          >
            <TextField
              label={`Break ${i + 1}`}
              type="number"
              value={b}
              onChange={(e) => handleChange(i, e.target.value)}
              size="small"
            />
            <IconButton
              onClick={() => handleRemove(i)}
              disabled={breaks.length === 1}
              size="small"
            >
              ×
            </IconButton>
          </Box>
        ))}
        <Button onClick={handleAdd} size="small">
          Add break
        </Button>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleApply} variant="contained">
          Apply
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DensitySliceDialog;
