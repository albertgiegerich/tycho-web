import { useCallback, useState } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";

interface BlurDialogProps {
  open: boolean;
  onClose: () => void;
  onApply: (kernelSize: number) => void;
}

const BlurDialog = ({ open, onClose, onApply }: BlurDialogProps) => {
  const [kernelSize, setKernelSize] = useState("3");

  const handleClose = useCallback(() => {
    setKernelSize("3");
    onClose();
  }, [onClose]);

  const handleApply = useCallback(() => {
    onApply(Number(kernelSize));
    handleClose();
  }, [kernelSize, onApply, handleClose]);

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>Blur</DialogTitle>
      <DialogContent>
        <TextField
          label="Kernel size"
          type="number"
          value={kernelSize}
          onChange={(e) => setKernelSize(e.target.value)}
          inputProps={{ min: 1, step: 2 }}
          size="small"
          sx={{ mt: 1 }}
        />
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

export default BlurDialog;
