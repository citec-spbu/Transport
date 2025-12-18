import { useForm } from "react-hook-form";
import PrimaryButton from "./PrimaryButton";

interface CodeFormProps {
  onSubmit: (code: string) => void;
  disabled?: boolean;
}

interface FormValues {
  code: string;
}

const CodeForm = ({ onSubmit, disabled }: CodeFormProps) => {
  const { register, handleSubmit } = useForm<FormValues>();

  return (
    <form
      onSubmit={handleSubmit((data: FormValues) => onSubmit(data.code))}
      className="flex flex-col gap-4 w-full"
    >
      <input
        {...register("code", { required: true, maxLength: 6 })}
        placeholder="Введите код"
        className="border p-3 rounded-4xl"
        disabled={disabled}
      />
      <div className="flex justify-end">
        <PrimaryButton type="submit" className="w-full py-2 text-lg">
          Подтвердить код
        </PrimaryButton>
      </div>
    </form>
  );
};

export default CodeForm;
