"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  useCategories, 
  useCreateCategory, 
  useUpdateCategory 
} from "@/lib/queries/categories";
import { fadeInUp, staggerContainer, staggerItem } from "@/lib/animations";
import { Tags, Plus, Trash2, Loader2, LayoutGrid, AlertCircle } from "lucide-react";

export default function CategoriesPage() {
  const [newName, setNewName] = useState("");
  
  // Backend verisini çekiyoruz
  const { data: categories, isLoading, isError, refetch } = useCategories(false);
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();

  const handleAdd = async () => {
    if (!newName.trim()) {
      toast.error("Category name cannot be empty");
      return;
    }
    try {
      await createMutation.mutateAsync({ name: newName.trim(), description: "" });
      toast.success("Category created successfully");
      setNewName("");
    } catch (e) {
      toast.error("Failed to create category");
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await updateMutation.mutateAsync({ 
        categoryId: id, 
        data: { is_active: false } 
      });
      toast.success("Category deactivated");
    } catch (e) {
      toast.error("Failed to update category");
    }
  };

  return (
    <motion.div 
      className="p-6 space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Category Management</h1>
        <LayoutGrid className="h-8 w-8 text-muted-foreground opacity-20" />
      </div>

      {/* Ekleme Bölümü */}
      <motion.div variants={fadeInUp}>
        <Card className="border-primary/20 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Plus className="h-5 w-5" /> Add New Category
            </CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Input 
              placeholder="Enter category name (e.g., Water Leak)..." 
              value={newName} 
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            />
            <Button onClick={handleAdd} disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Add Category"
              )}
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      {/* Liste Bölümü */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          // Yüklenme durumu için skeleton
          Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))
        ) : isError ? (
          <div className="col-span-full py-10 text-center space-y-3">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <p className="text-muted-foreground">Failed to load categories.</p>
            <Button onClick={() => refetch()} variant="outline">Try Again</Button>
          </div>
        ) : (
          // HATA ÇÖZÜMÜ: categories?.items?.map kullanımı
          categories?.items?.map((cat: any) => (
            <motion.div key={cat.id} variants={staggerItem}>
              <Card className={`group transition-all hover:shadow-md ${!cat.is_active ? 'opacity-50 grayscale' : ''}`}>
                <CardContent className="p-5 flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/5 rounded-lg text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                      <Tags className="h-4 w-4" />
                    </div>
                    <span className="font-semibold">{cat.name}</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => handleDeactivate(cat.id)}
                    className="text-muted-foreground hover:text-red-500 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>

      {(!isLoading && !categories?.items?.length) && (
        <div className="text-center py-20 bg-muted/20 rounded-2xl border border-dashed">
          <p className="text-muted-foreground">No categories found. Start by adding one above.</p>
        </div>
      )}
    </motion.div>
  );
}